import requests_cache

requests_cache.install_cache("cache")

import grequests
import requests

from py.cli import expose


@expose
async def foo():
    rs = [
        grequests.get(f"https://httpbin.org/status/{code}") for code in range(200, 206)
    ]
    for index, response in grequests.imap_enumerated(rs, size=5):
        print(index, response)
