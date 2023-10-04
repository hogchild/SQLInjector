#!/usr/bin/env python3.12
# test_cookie_injector.py ver 9.0
import unittest
from types import SimpleNamespace

from SQLInjector import cookie_injector_setup


class MyTestCase(unittest.TestCase):
    def test_validate_url_valid_data(self):
        """Submits a valid url, through a SimpleNamespace object, to the 'validate_url'
        method, and checks if it returns True or a ValidationError instance."""
        setup = cookie_injector_setup.CookieInjSetup()
        target_url = SimpleNamespace()
        target_url.name = "target_url"
        urls = [
            "ftp://trecca.org", "https://kamapuaa.it", "https://portswigger.net/web-security/sql-injection/cheat-sheet",
            "https://chat.openai.com/c/c979b52a-bc61-4d8f-8590-963e5b1e28c4",
            "https://www.udemy.com/course/learn-bug-bounty-hunting-web-security-testing-from-scratch/learn/lecture/"
            "34126040#questions", "https://kamapuaa.it/pagamento/order-received/3743/?key=wc_order_nD5QGXleUUDF6",
            "https://kamapuaa.it/wp-login.php?loggedout=true&wp_lang=it_IT"
        ]
        for url in urls:
            setup.options[target_url.name] = url
            is_valid_url = setup.validate_url(target_url)
            self.assertTrue(is_valid_url)  # add assertion here

    def test_validate_url_invalid_data(self):
        """Submits an invalid url, through a SimpleNamespace object, to the 'validate_url'
        method, and checks if it returns True or a ValidationError instance."""
        setup = cookie_injector_setup.CookieInjSetup()
        target_url = SimpleNamespace()
        target_url.name = "target_url"
        urls = [
            "https:puaa.it", 0, {"a": "b"}, [1, "a"], "&<sudo -i", "raise Exception('raised error')",
            ("a" * 1000), sorted([22, 13, 48, 51, 4, 9, 8, 18, 1]), (1, 2), 99999, "abc",
            "9999**99999999999999999999"
        ]
        for url in urls:
            setup.options[target_url.name] = url
            is_valid_url = setup.validate_url(target_url)
            self.assertFalse(is_valid_url)

    def test_validate_int_valid_data(self):
        """Submits a valid integer, through a SimpleNamespace object, to the 'validate_int'
        method, and checks if it returns True or a ValueError instance."""
        setup = cookie_injector_setup.CookieInjSetup()
        max_threads = SimpleNamespace()
        max_threads.name = "max_threads"
        max_threads_values = [num for num in range(1, 25)]
        for max_threads_value in max_threads_values:
            setup.options[max_threads.name] = max_threads_value
            is_valid_int = setup.validate_int(max_threads)
            self.assertTrue(is_valid_int)  # add assertion here

    def test_validate_int_invalid_data(self):
        """Submits an invalid integer, through a SimpleNamespace object, to the 'validate_int'
        method, and checks if it returns True or a ValueError instance."""
        setup = cookie_injector_setup.CookieInjSetup()
        max_threads = SimpleNamespace()
        max_threads.name = "max_threads"
        max_threads_values = [0, {"a": "b"}, [1, "a"], "&<sudo -i", sorted([22, 13, 48, 51, 4, 9, 8, 18, 1]), (1, 2),
                              99999, "abc", "9999**99999999999999999999"]
        for max_threads_value in max_threads_values:
            setup.options[max_threads.name] = max_threads_value
            is_valid_int = setup.validate_int(max_threads)
            self.assertFalse(is_valid_int)  # add assertion here

    def test_validate_input_data_valid_and_invalid_data(self):
        """Tests if object types are routed correctly to their intended method."""
        # Test url type.
        setup = cookie_injector_setup.CookieInjSetup()
        target_url = SimpleNamespace()
        target_url.name = "target_url"
        target_url.type = "url"
        setup.options[target_url.name] = "test_wrong_url_format"
        is_data_being_validated_as_url = setup.validate_input_data(target_url)
        self.assertFalse(is_data_being_validated_as_url)
        setup.options[target_url.name] = "https://kamapuaa.it"
        is_data_being_validated_as_url = setup.validate_input_data(target_url)
        self.assertTrue(is_data_being_validated_as_url)

        # Test string type.
        setup = cookie_injector_setup.CookieInjSetup()
        inject_code = SimpleNamespace()
        inject_code.name = "inject_code"
        inject_code.type = "str"
        setup.options[inject_code.name] = None
        is_data_being_validated_as_str = setup.validate_input_data(inject_code)
        self.assertTrue(is_data_being_validated_as_str)
        setup.options[inject_code.name] = "test_string!£$%/&/())==?"
        is_data_being_validated_as_str = setup.validate_input_data(inject_code)
        self.assertTrue(is_data_being_validated_as_str)
        setup.options[target_url.name] = [{"https://kamapuaa.it": None}, "test", 3]
        is_data_being_validated_as_str = setup.validate_input_data(inject_code)
        self.assertTrue(is_data_being_validated_as_str)

        # Test int type.
        setup = cookie_injector_setup.CookieInjSetup()
        passwd_length = SimpleNamespace()
        passwd_length.name = "passwd_length"
        passwd_length.type = "int"
        # Invalid string
        setup.options[passwd_length.name] = "not_an_int"
        is_data_being_validated_as_int = setup.validate_input_data(passwd_length)
        self.assertFalse(is_data_being_validated_as_int)
        # Valid int
        setup.options[passwd_length.name] = 24
        is_data_being_validated_as_int = setup.validate_input_data(passwd_length)
        self.assertTrue(is_data_being_validated_as_int)
        # Number over 24
        setup.options[passwd_length.name] = 25
        is_data_being_validated_as_int = setup.validate_input_data(passwd_length)
        self.assertFalse(is_data_being_validated_as_int)
        # String number between 1-24.
        setup.options[passwd_length.name] = "14"
        is_data_being_validated_as_int = setup.validate_input_data(passwd_length)
        self.assertTrue(is_data_being_validated_as_int)
        # String number over 24.
        setup.options[passwd_length.name] = "34"
        is_data_being_validated_as_int = setup.validate_input_data(passwd_length)
        self.assertFalse(is_data_being_validated_as_int)

    # @patch("builtins.input", side_effect=["e", "q"])
    # def test_validate_choice(self, mock_input):
    #     print("mok input", mock_input)
    #     setup = cookie_injector_setup.CookieInjSetup()
    #     setup.confirm = "n"
    #     option_obj = SimpleNamespace()
    #     option_obj.name = "target_url"
    #     setup.options[option_obj.name] = "http://kama.it"
    #     option_obj.message = "test_message"
    #     option_obj.type = "str"
    #     option_obj.show_message = "test_show_message"
    #     option_obj.confirm_text = "test_confirm_text"
    #     option_obj.show_confirm_text = "test_confirm_text"
    #
    #     validate_choice_ok = setup.validate_choice(option_obj)
    #     exit_message = option_obj.message  # [edit/e/quit/q] (edit):"  # "Is the url correct? [y/n] (y):"  #
    #     self.assertTrue(validate_choice_ok)

    def test_set_corrected_option(self):
        pass


if __name__ == '__main__':
    unittest.main()
