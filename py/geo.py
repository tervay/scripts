from tabulate import tabulate

from py.cli import expose, pprint
from py.osrm import event_matrix, matrix
from py.tba import EventType
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
            if (event.event_type not in EventType.SEASON_EVENT_TYPES) or (
                event.event_type == EventType.CMP_FINALS
            ):
                continue

            teams = [t async for t in tpa.get_event_teams(event_key=event.key)]
            if len(teams) == 0:
                continue

            m = event_matrix(event=event, teams=teams)
            for k, v in m.items():
                if v is not None:
                    drives.append((event.key, k, v))

    for e, t, seconds in sorted(drives, key=lambda t: -t[-1])[:100]:
        print(
            f"{t.rjust(3 + 4)} -> {e.rjust(4 + 6)} ~{str(round(seconds / (60 * 60), 1)).rjust(2 + 2)} hrs"
        )


@expose
async def test(tkey, ekey):
    async with tpa_cm() as tpa:
        team = await tpa.get_team(team_key=tkey)
        event = await tpa.get_event(event_key=ekey)
        teams = [t async for t in tpa.get_event_teams(event_key=event.key)]
        pprint(event_matrix(event=event, teams=teams))


@expose
async def isolated_events(year):
    dists = {}
    async with tpa_cm() as tpa:
        async for bar, event in tqdm_bar_async(
            [e async for e in tpa.get_events_by_year(year=year)]
        ):
            bar.set_description(event.key)
            if event.event_type not in EventType.SEASON_EVENT_TYPES:
                continue

            teams = [t async for t in tpa.get_event_teams(event_key=event.key)]
            if len(teams) == 0:
                continue

            m = event_matrix(event=event, teams=teams)
            dists[event.key] = [m[t.key] for t in teams if m[t.key] is not None]

    dists = {k: (sum(v) / len(v)) / (60 * 60) for k, v in dists.items()}
    pprint(sorted(dists.items(), key=lambda t: -t[1]))
