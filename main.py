import asyncio
from sys import argv

from grpclib.server import Server

import py.graphing
import py.tba_proto
import py.teams
from py.cli import run_main
from py.tpa import TPAService


async def start_server():
    server = Server([TPAService()])
    print("starting")
    await server.start("127.0.0.1", "1337")
    print("waiting")
    await server.wait_closed()
    asyncio.create_task()


if __name__ == "__main__":
    if len(argv) >= 2 and argv[1] == "tpa":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server())
    else:
        asyncio.get_event_loop().run_until_complete(run_main(argv[1:]))
