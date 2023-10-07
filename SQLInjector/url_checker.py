#!/usr/bin/env python3.12
# url_checker.py
import sys
from urllib.parse import urlparse
import requests
from rich.console import Console

table_data = [
    ("1xx (Informational)", "100 Continue", "Non-Fatal Error",
     "Indicates the server received the initial part of the request."),
    ("", "101 Switching Protocols", "Non-Fatal Error",
     "The server is changing protocols, typically in response to an Upgrade request from the client."),
    ("", "102 Processing", "Non-Fatal Error",
     "This code indicates that the server has received and is processing the request, but no response is available yet."),
    ("", "103 Early Hints", "Non-Fatal Error",
     "A hint that the server is pushing responses proactively, providing early information before the final response."),
    ("2xx (Successful)", "200 OK", "Non-Fatal Error", "The server processed the request successfully."),
    ("", "201 Created", "Non-Fatal Error", "A new resource was successfully created on the server."),
    ("", "202 Accepted", "Non-Fatal Error",
     "The request has been accepted for processing, but processing might not be complete."),
    ("", "203 Non-Authoritative Information", "Non-Fatal Error",
     "The server is a transforming proxy and has modified the response."),
    ("", "204 No Content", "Non-Fatal Error",
     "The server successfully processed the request, but there's no response body."),
    ("", "205 Reset Content", "Non-Fatal Error",
     "Instructs the client to reset the document view, such as clearing form input fields."),
    ("", "206 Partial Content", "Non-Fatal Error",
     "The server is returning part of the requested resource, typically for range requests."),
    ("", "207 Multi-Status", "Non-Fatal Error", "A status for multiple independent operations."),
    ("", "208 Already Reported", "Non-Fatal Error",
     "Used inside a DAV: propstat response element to avoid enumerating the internal members of multiple bindings to the same collection repeatedly."),
    ("", "226 IM Used", "Non-Fatal Error",
     "The server has fulfilled a GET request for the resource, and the response is a representation of the result of one or more instance-manipulations applied to the current instance."),
    ("3xx (Redirection)", "300 Multiple Choices", "Non-Fatal Error",
     "Indicates multiple options for the resource from which the client may choose."),
    ("", "301 Moved Permanently", "Non-Fatal Error",
     "Indicates that the resource has been permanently moved to a new location, and the client should issue a new request to that location."),
    ("", "302 Found", "Non-Fatal Error",
     "Indicates that the resource is temporarily located at another location, and the client should issue a new request to that location."),
    ("", "303 See Other", "Non-Fatal Error",
     "Indicates that the response to the request can be found under another URI."),
    ("", "304 Not Modified", "Non-Fatal Error",
     "Indicates that the resource has not been modified since the version specified by the request headers."),
    ("", "305 Use Proxy", "Non-Fatal Error",
     "Indicates that the requested resource must be accessed through the proxy given by the Location field."),
    ("", "307 Temporary Redirect", "Non-Fatal Error",
     "Indicates that the request should be repeated with another URI, but the client should do this only temporarily."),
    ("", "308 Permanent Redirect", "Non-Fatal Error",
     "The request and all future requests should be repeated using another URI."),
    ("4xx (Client Errors)", "400 Bad Request", "Non-Fatal Error",
     "Indicates a client-side error, but the server is still functional."),
    ("", "401 Unauthorized", "Non-Fatal Error", "Authentication is required, but the server is functional."),
    ("", "402 Payment Required", "Non-Fatal Error", "This code is reserved for future use."),
    ("", "403 Forbidden", "Non-Fatal Error",
     "Access to the requested resource is forbidden, but the server is operational."),
    ("", "404 Not Found", "Non-Fatal Error", "The requested resource is not found, but the server is running."),
    ("", "405 Method Not Allowed", "Non-Fatal Error",
     "The server doesn't support the requested HTTP method, but it's operational."),
    ("", "406 Not Acceptable", "Non-Fatal Error",
     "The requested resource is capable of generating only content not acceptable according to the Accept headers sent in the request."),
    ("", "407 Proxy Authentication Required", "Non-Fatal Error",
     "The client must first authenticate itself with the proxy."),
    ("", "408 Request Timeout", "Non-Fatal Error", "The request timed out, but the server is functional."),
    ("", "409 Conflict", "Non-Fatal Error",
     "Indicates that the request could not be completed due to a conflict with the current state of the target resource."),
    ("", "410 Gone", "Non-Fatal Error",
     "Indicates that the requested resource is no longer available at the server and no forwarding address is known."),
    ("", "411 Length Required", "Non-Fatal Error",
     "The server requires a Content-Length to be included in the request."),
    ("", "412 Precondition Failed", "Non-Fatal Error",
     "Indicates that one or more preconditions given in the request header fields evaluated to false when tested on the server."),
    ("", "413 Request Entity Too Large", "Non-Fatal Error",
     "Indicates that the server is refusing to process a request because the request entity is larger than the server is willing or able to process."),
    ("", "414 Request-URI Too Long", "Non-Fatal Error",
     "Indicates that the server is refusing to process a request because the request URI is longer than the server is willing to interpret."),
    ("", "415 Unsupported Media Type", "Non-Fatal Error",
     "Indicates that the server is refusing to service the request because the request entity's media type is not supported by the server."),
    ("", "416 Requested Range Not Satisfiable", "Non-Fatal Error",
     "Indicates that none of the ranges in the request's Range header field overlap the current extent of the selected resource."),
    ("", "417 Expectation Failed", "Non-Fatal Error",
     "Indicates that the expectation given in the request's Expect header field could not be met."),
    (
        "", "418 I'm a Teapot", "Non-Fatal Error",
        "A joke status code, not meant to be implemented by real HTTP servers."),
    ("", "421 Misdirected Request", "Non-Fatal Error",
     "The request was directed at a server that is not able to produce a response."),
    ("", "422 Unprocessable Entity", "Non-Fatal Error",
     "Indicates that the server understands the content type of the request entity, and the syntax of the request entity is correct, but it was unable to process the contained instructions."),
    ("", "423 Locked", "Non-Fatal Error", "Indicates that the source or destination resource is locked."),
    ("", "424 Failed Dependency", "Non-Fatal Error",
     "Indicates that the method could not be performed on the resource because the requested action depended on another action and that action failed."),
    ("", "425 Too Early", "Non-Fatal Error",
     "Indicates that the server is unwilling to risk processing a request that might be replayed."),
    ("", "426 Upgrade Required", "Non-Fatal Error",
     "Indicates that the server refuses to perform the request using the current protocol but might be willing to do so after the client upgrades to a different protocol."),
    ("", "428 Precondition Required", "Non-Fatal Error",
     "Indicates that the server requires the request to be conditional."),
    ("", "429 Too Many Requests", "Non-Fatal Error", "The user has sent too many requests in a given amount of time."),
    ("", "431 Request Header Fields Too Large", "Non-Fatal Error",
     "Indicates that the server is unwilling to process the request because its header fields are too large."),
    ("", "451 Unavailable For Legal Reasons", "Non-Fatal Error",
     "Indicates that the server is denying access to the resource as a consequence of a legal demand."),
    ("5xx (Server Errors)", "500 Internal Server Error", "Potentially Fatal Error",
     "Indicates a server-side error; the server may have issues, but it's still running."),
    ("", "501 Not Implemented", "Potentially Fatal Error",
     "Indicates that the server does not support the functionality required to fulfill the request."),
    ("", "502 Bad Gateway", "Potentially Fatal Error",
     "Indicates a gateway or proxy error, but it doesn't necessarily mean the backend server is down."),
    ("", "503 Service Unavailable", "Potentially Fatal Error",
     "The server or a proxy is temporarily unavailable, but it may come back online."),
    ("", "504 Gateway Timeout", "Potentially Fatal Error",
     "Indicates that a server acting as a gateway or proxy did not receive a timely response from an upstream server. This can suggest a server issue."),
    ("", "505 HTTP Version Not Supported", "Potentially Fatal Error",
     "Indicates that the server does not support the HTTP protocol version used in the request. This may suggest a configuration issue or an outdated server."),
    ("", "506 Variant Also Negotiates", "Non-Fatal Error",
     "Indicates that the server has an internal configuration error: the chosen variant resource is configured to engage in transparent content negotiation itself, and is therefore not a proper end point in the negotiation process."),
    ("", "507 Insufficient Storage", "Non-Fatal Error",
     "Indicates that the server is unable to store the representation needed to complete the request."),
    ("", "508 Loop Detected", "Non-Fatal Error",
     "Indicates that the server detected an infinite loop while processing the request."),
    ("", "510 Not Extended", "Non-Fatal Error",
     "Indicates that further extensions to the request are required for the server to fulfill it."),
    ("", "511 Network Authentication Required", "Non-Fatal Error",
     "Indicates that the client needs to authenticate to gain network access."),
]


class UrlChecker:
    def __init__(self, target_url: str | bytes) -> None:
        self.parsed_url = None
        self.response = None
        self.c = Console()
        self.url = target_url
        self.get_status_by_status_code = None
        self.code = None

    def assign_group(self):
        for group, *others in table_data:
            if group:
                code_id = str(self.code).split()[0][0]
                if str(group).startswith(code_id):
                    assigned_group = group
                    return assigned_group
    def http_status_responses(self) -> str:
        """
        Returns the whole record of the http status response.
        It searches from the status code, so self.get_status_by_status_code
        variable needs to be set to a specific status_code (int | str).
        :return: f"{group} | {code} | {category} | {description}"
        """
        for group, self.code, category, description in table_data:
            if str(self.get_status_by_status_code) in str(self.code):
                if not group:
                    assigned_group = self.assign_group()
                    return f"{assigned_group} | {self.code} | {category} | {description}"
                else:
                    return f"{group} | {self.code} | {category} | {description}"

    def check_url_format(self):
        self.parsed_url = urlparse(self.url)

    def check_url(self):
        try:
            self.response = requests.head(self.url)
            self.get_status_by_status_code = self.response.status_code
            http_status = self.http_status_responses()
            self.c.print(http_status, self.response.status_code)
            self.c.print(self.response.headers, "\n")
        except requests.RequestException as e:
            self.c.print(f"Error: {e}")
            sys.exit(1)


def main():
    urls =[
        # "https://google.com/",
        "https://sivanandamusic.it/",
        "https://kamapuaa.it/",
        # "https://0a91002a045a58ed8325199c005b0008.web-security-academy.net/product?productId=3"
    ]
    for url in urls:
        uc = UrlChecker(url)
        uc.check_url()
    # uc = UrlChecker("https://0ad500c5035e0be18303851d0016008c.web-security-academy.net/product?productId=4")
    # uc.check_url()


if __name__ == '__main__':
    main()
