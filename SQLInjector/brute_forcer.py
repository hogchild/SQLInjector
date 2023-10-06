#!/usr/bin/env python3.12
# brute_forcer.py

from types import SimpleNamespace


class BruteForcer:
    def __init__(self, password_length, payload_char_set, inject_code):
        self.characters_seq_numbers = None
        self.password_length = int(password_length)
        self.character_seq_numbers = [numb for numb in range(1, self.password_length + 1)]
        self.payload_char_set = payload_char_set
        self.inject_code = inject_code
        self.payload_tag_1 = "{char_numb}"
        self.payload_tag_2 = "{character}"
        self.payload_kit = None

    def brute_force(self):
        for char_seq_number in self.character_seq_numbers:
            for char in self.payload_char_set:
                code = self.inject_code.replace(self.payload_tag_1, str(char_seq_number)).replace(self.payload_tag_2, str(char))
                self.payload_kit = SimpleNamespace(inject_code=code, sequence_num=char_seq_number, character=char)
                yield self.payload_kit
