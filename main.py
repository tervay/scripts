import asyncio
from sys import argv

import requests_cache
import pretty_errors
from colorama import init
from grpclib.server import Server

import py.awards
import py.codegen
import py.event_gen
import py.geo
import py.graphing
import py.html
import py.scout
import py.sim
import py.teams
from py.cli import run_main
from py.tpa import TPAService

init()
requests_cache.install_cache("requests_cache")


async def start_server():
    server = Server([TPAService()])
    print("starting")
    await server.start("127.0.0.1", "1337")
    print("waiting")
    await server.wait_closed()


if __name__ == "__main__":
    if len(argv) >= 2 and argv[1] == "tpa":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server())
    else:
        asyncio.get_event_loop().run_until_complete(run_main(argv[1:]))
