import unittest
from unittest.mock import patch

import requests.cookies

import SQLInjector.custom_errors
from SQLInjector.cookie_injector_core import CookieInjector


class TestCookieInjectorCore(unittest.TestCase):
    def test_get_response(self):
        cookie_injector = CookieInjector(
            "https://google.com",
            "Welcome",
            "TrackingID"
        )
        # Assert status code 200 with valid URL and self.cookies == None.
        cookie_injector.cookies = None
        cookie_injector.get_response()
        self.assertEqual(cookie_injector.response.status_code, 200)  # add assertion here

        # Assert self.cookies not None.
        cookie_injector.extract_cookies()
        self.assertNotEqual(cookie_injector.cookies, None)

        # Assert get request with cookies returns status code 200.
        cookie_injector.get_response()
        self.assertTrue(cookie_injector.response.status_code, 200)

        # Assert invalid URL raises error.
        cookie_injector.target_url = "http/google.it"
        try:
            cookie_injector.get_response()
        except SQLInjector.custom_errors.CookieInjectorGetResponseError as e:
            self.assertTrue(isinstance(e, SQLInjector.custom_errors.CookieInjectorGetResponseError))

    def test_extract_cookies(self):
        cookie_injector = CookieInjector(
            "https://google.com",
            "Welcome",
            "TrackingID"
        )
        cookie_injector.get_response()
        cookie_injector.extract_cookies(print_cookies=False)
        self.assertIsNotNone(cookie_injector.cookies)

    @patch("rich.console.Console.print")
    def test_print_cookies(self, mock_rich_print):
        """Tests if print_cookies() func printing cookies properly"""
        cookie_injector = CookieInjector(
            "https://google.com",
            "Welcome",
            "TrackingID"
        )
        cookie_injector.get_response()
        cookie_injector.extract_cookies()
        cookie_injector.print_cookies()
        captured_output = mock_rich_print.call_args_list
        self.assertIn("RequestsCookieJar", str(captured_output[0]))
        cookie_injector.cookies = None
        self.assertIsNone(cookie_injector.cookies)

    def test_copy_cookie(self):
        cookie_injector = CookieInjector(
            "https://google.com",
            "Welcome",
            "TrackingID"
        )
        pass


if __name__ == '__main__':
    unittest.main()
