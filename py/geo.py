from tabulate import tabulate

from py.cli import expose, pprint
from py.osrm import matrix, event_matrix
from py.tpa import tpa_cm
from py.util import MAX_TEAMS_PAGE_NUM, flatten_lists_async, tqdm_bar_async


@expose
async def longdrives():
    drives = []
    skipped = 0
    async with tpa_cm() as tpa:
        async for bar, event in tqdm_bar_async(
            await flatten_lists_async(
                [tpa.get_events_by_year(year=i) for i in range(2019, 2020)]
            )
        ):
            bar.set_description(event.key)
            teams = [t async for t in tpa.get_event_teams(event_key=event.key)]
            if len(teams) == 0:
                continue

            m = event_matrix(event=event, teams=teams)
            for k, v in m.items():
                drives.append((event.key, k, v))

    pprint(sorted(drives, key=lambda t: -t[-1])[:25])


@expose
async def test(tkey, ekey):
    async with tpa_cm() as tpa:
        team = await tpa.get_team(team_key=tkey)
        event = await tpa.get_event(event_key=ekey)
        teams = [t async for t in tpa.get_event_teams(event_key=event.key)]
        pprint(event_matrix(event=event, teams=teams))
