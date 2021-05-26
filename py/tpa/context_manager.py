from contextlib import asynccontextmanager

from grpclib.client import Channel
from protos import TpaStub

ch = Channel(host="127.0.0.1", port=1337)
stub = TpaStub(channel=ch)


@asynccontextmanager
async def tpa_cm():
    try:
        yield stub
    finally:
        pass
