#!/usr/bin/env python3.12
# brute_forcer.py ver 1.1


class CookieInjectorGetResponseError(Exception):
    def __init__(self, message="Error communicating with server."):
        super().__init__(message)
