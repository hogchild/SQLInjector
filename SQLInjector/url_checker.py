#!/usr/bin/env python3.12
# url_checker.py
import csv
import json
import logging
import sys
from typing import Any

import click
import requests
from rich.console import Console
from rich.markdown import Markdown

from SQLInjector.custom_errors import InvalidURLError, InvalidInputListError, HTTP5xxResponseException, HTTP4xxResponseException, \
    HTTP3xxResponseException
from SQLInjector.reverse_logger import (
    ReverseLogger, log_error_and_raise_exception, filename_parser, log_error
)
from data.input.data_sources import full_table_data, validation_result_tab, check_result_tab, urls_to_check_tuple

filename, log_filepath = filename_parser(log_file_name=__file__)
rev_log = ReverseLogger(
    logger_name=filename,
    log_file_path=log_filepath,
    logging_level=logging.DEBUG,
    encoding="utf-8"
)


class UrlChecker:
    def __init__(
            self, urls: tuple = None, url_list: list = None, outfile: bool = False,
            validation_result_table: str = validation_result_tab, check_result_table: str = check_result_tab
    ) -> None:
        self.outfile: bool = outfile
        self.c: Console = Console()
        self.data_table: list = full_table_data
        self.url: str = ""
        self.url_list: list = url_list
        self.urls: tuple = urls
        self.output_report: list | tuple = []
        self.valid_url_records: list = []
        self.invalid_url_records: list = []
        self.response: requests.Response = requests.Response()
        self.status_record: str = ""
        self.group: str = ""
        self.status_record_str: str = ""
        self.validation_result_table = validation_result_table
        self.check_result_table = check_result_table
        self.url_is_valid = None

    def process_urls(self) -> None:
        """
        Processes command line arguments and options. Initiates class variables and URLs lists.
        :return: None
        """
        # If there is a self.url_list (click option), checks if it's a list as the app takes json.loads input.
        if self.url_list is not None:
            try:
                list(json.dumps(self.url_list))
            except TypeError as e:
                error_message = (
                    f"Type '{type(self.url_list)}' not allowed {e}."
                    f"""Enter a list in JSON syntax (i.e.: '["url_1", "url_2"]')"""
                )
                # raise InvalidInputListError(error_message)
                log_error_and_raise_exception(rev_log, error_message, InvalidInputListError(error_message))
            if not isinstance(self.url_list, list):
                error_message = (
                    f"Type '{type(self.url_list)}' not allowed. "
                    f"""Enter a list in JSON syntax (i.e.: '["url_1", "url_2"]')"""
                )
                log_error_and_raise_exception(rev_log, error_message, InvalidInputListError(error_message))
        else:
            self.url_list = []
        # These are URLs passed via click positional ARGUMENT, no option i.e.: "-c".
        # We append each urlin the iterable in the self.url_list
        if self.urls:
            # Append all positional arg URL to self.url_list
            for url in self.urls:
                self.url_list.append(url)

    def check_url_format(self) -> bool | Exception:
        import validators
        if not validators.url(self.url):
            error_message = self.url
            self.url_is_valid = validators.url(self.url)
            log_error_and_raise_exception(
                logger_obj=rev_log,
                error_message=error_message,
                exception=InvalidURLError(error_message),
            )
        else:
            return True

    def validate(self):
        try:
            self.url_is_valid = self.check_url_format()
        except InvalidURLError as e:
            message = f"| Error validating the URL | {e} | {self.url_is_valid is True} | \n"
            self.validation_result_table += message
            stripped_message = tuple(message.split("|")[1:-1:1])
            self.output_report.append(stripped_message)
        else:
            message = f"| Validation succeeded | {self.url} | {self.url_is_valid} | \n"
            self.validation_result_table += message
            stripped_message = tuple(message.split("|")[1:-1:1])
            self.output_report.append(stripped_message)

    def write_outfile(self):
        outfile_name = "data/output/check_url_out.csv"
        with open(outfile_name, "w") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(("Outcome", "URL", "Validation Passed"))
            for record in self.output_report:
                writer.writerow(record)
        self.c.print(f"Created outfile '{outfile_name}'.")

    def validate_url(self) -> tuple[tuple[str]]:
        try:
            self.process_urls()
        except InvalidInputListError as e:
            error_message = f"UNABLE to process URLs: {e}."
            self.c.print(error_message)
            sys.exit(1)
        else:
            # try:
            # Append actual result tuples to self.output_report
            for self.url in self.url_list:
                self.validate()
            # except TypeError as e:
            #     error_message = (
            #         f"unable to process request: {e}.\n"
            #         f"No URLs submitted: '{self.urls}'. Use '--help' for usage."
            #     )
            #     log_error_and_raise_exception(rev_log, error_message, InvalidURLError(error_message))
            self.output_report = tuple(self.output_report)
            if self.outfile:
                if self.output_report:
                    self.write_outfile()
                else:
                    error_message = (
                        f"Output report empty: '{self.output_report}'. "
                        f"Maybe you forgot to submit an URL: '{self.url}'."
                    )
                    log_error_and_raise_exception(rev_log, error_message, InvalidInputListError(error_message))
            print()
            self.c.print(Markdown("---\n"))
            self.c.print(Markdown(self.validation_result_table))
            return self.output_report

    def get_http_status_record(self):
        for self.group, status_code, category, description in self.data_table:
            if str(self.response.status_code) in str(status_code):
                return self.group, status_code, category, description

    # def process_response(self):
    #     if self.group.startswith(str(5)):
    #         error_message = f"The HTTP response category is {self.group}. The server may have problems."
    #         log_error_and_raise_exception(rev_log, error_message, HTTP5xxResponseException(error_message))
    #     elif self.group.startswith(str(4)):
    #         info_message = f"The HTTP response category is {self.group}. The server could still be ok."
    #         log_error_and_raise_exception(rev_log, info_message, HTTP4xxResponseException(info_message))
    #     elif self.group.startswith(str(3)):
    #         info_message = (f"The HTTP response category is {self.group}. The server has redirected our request "
    #                         f"to a new address.")
    #         log_error_and_raise_exception(rev_log, info_message, HTTP3xxResponseException(info_message))

    def process_response(self):
        pass

    def check_url(self):
        try:
            self.validate_url()
        except InvalidURLError as e:
            error_message = f"URL validation FAILED: {e}."
            log_error_and_raise_exception(rev_log, error_message, TypeError(error_message))
        else:
            for record in self.output_report:
                if "True" in record[2]:
                    self.valid_url_records.append(record)
                else:
                    self.invalid_url_records.append(record)
            # self.c.print("Invalid (format) URLs:", self.invalid_url_records, style="red")
            # self.c.print("Valid (format) URLs:", self.valid_url_records, style="green")
            self.output_report = tuple(self.valid_url_records)
            # self.c.print("Out Record:", list(self.output_report))
            total_requests = len(self.output_report)
            request_left = total_requests
            for url_record in self.output_report:
                self.url, self.url_is_valid = url_record[1:]
                try:
                    self.response = requests.head(self.url.strip())
                except requests.RequestException as e:
                    self.c.print(f"HEAD request failed for URL {self.url}: {e}")
                else:
                    self.c.print(
                        f"Sending head requests to URL '{self.url}'. "
                        f"Request left {request_left} total requests {total_requests}. ",
                        end="\r"
                    )
                    request_left -= 1
                self.status_record = self.get_http_status_record()
                self.status_record_str = ', '.join(self.get_http_status_record())
                message = f"| {self.status_record[1]} | {self.url} | {self.status_record[2]} | {self.status_record[3]} | \n"
                self.check_result_table += message
            self.c.print(Markdown("---\n"))
            print()
            self.c.print(Markdown(self.check_result_table))
            # try:
            self.process_response()
            # except HTTP5xxResponseException as e:
            #     error_message = Markdown(f"Server Error: \n- Error fetching the URL {self.url}.\n\t- {e}")
            #     log_error(rev_log, error_message)
            #     print()
            # except HTTP4xxResponseException as e:
            #     error_message = Markdown(f"Client Error: \n- Error fetching the URL {self.url}.\n\t- {e}")
            #     log_error(rev_log, error_message)
            #     print()
            # except HTTP3xxResponseException as e:
            #     info_message = Markdown(f"Redirection: \n- Request to URL {self.url} was redirected.\n\t- {e}")
            #     log_error(rev_log, info_message)
            #     print()




@click.command(
    help=(
            "This app is an URL checker. It checks the validity of an URL, and checks the target host with head or get "
            "requests."
    )
)
@click.argument(
    "urls",
    nargs=-1,
    required=False,
    metavar="[url_1] [url_2] [...]"
)
@click.option(
    "-l", "--url-list", "url_list",
    help='Pass a list of URLs to check.',
    # default=json.dumps([]),
    # default=json.dumps(urls_to_check),
    # default=json.dumps(urls_to_check_tuple),
    required=False,
    type=json.loads
)
@click.option(
    "-c", "--check-format", "check_format",
    help="Validate only the URL format, don't send any requests.",
    is_flag=True,
    required=False,
    default=False,
)
@click.option(
    "-o", "--outfile",
    help="Write output to data/output/check_url_out.csv.",
    is_flag=True,
    required=False,
    default=False,
)
def main(urls, url_list, outfile, check_format):
    uc = UrlChecker(urls, url_list, outfile)
    if check_format:
        try:
            uc.validate_url()
        except TypeError as e:
            Console().print(f"URL validation FAILED: {e}.")
            sys.exit(1)

    else:
        try:
            uc.check_url()
        except TypeError as e:
            Console().print(f"URL check FAILED: {e}.")
            sys.exit(1)


if __name__ == '__main__':
    main()
