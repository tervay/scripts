import asyncio
import os
import warnings
from datetime import timedelta
from sys import argv

import colorama
import humanize
import requests_cache
from grpclib.server import Server
from rich.traceback import install

import py.awards
import py.codegen
import py.elo
import py.event_gen
import py.events
import py.geo
import py.graphing
import py.html_
import py.matches
import py.cope
import py.scout
import py.sheets
import py.justin
import py.sim
import py.teams
import py.test
import py.write
import py.weekly
from py.cli import run_main
from py.tpa import TPAService
from py.util import CURRENT_YEAR

install(show_locals=True)

warnings.filterwarnings("ignore")

colorama.init()

requests_cache.install_cache(
    "requests_cache",
    urls_expire_after={
        f"*{CURRENT_YEAR}*": timedelta(days=30),
        "*": -1,
    },
)


async def start_server():
    server = Server([TPAService()])
    cache_size = humanize.naturalsize(os.stat("requests_cache.sqlite").st_size)
    print(f"starting with cache size of {cache_size}")
    await server.start("127.0.0.1", "1337")
    print("waiting")
    await server.wait_closed()


if __name__ == "__main__":
    if len(argv) >= 2 and argv[1] == "tpa":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server())
    else:
        asyncio.get_event_loop().run_until_complete(run_main(argv[1:]))
