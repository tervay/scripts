from py.cli import expose
from py.tpa import tpa_cm


@expose
async def test(mkey):
    async with tpa_cm() as tpa:
        print(await tpa.get_match(match_key=mkey))



