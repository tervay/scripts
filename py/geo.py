import osrm
from tabulate import tabulate

from py.cli import expose, pprint
from py.tpa import tpa_cm
from py.util import MAX_TEAMS_PAGE_NUM, flatten_lists_async, tqdm_bar_async


@expose
async def geocode_teams():
    unfixed = []

    async with tpa_cm() as tpa:
        async for bar, team in tqdm_bar_async(
            await flatten_lists_async(
                [
                    tpa.get_teams_by_year(page_num=i, year=2020)
                    for i in range(MAX_TEAMS_PAGE_NUM)
                ]
            )
        ):
            print(f"{team.key.rjust(3 + 4)} {team.lat}, {team.lng}")


@expose
async def geocode_events():
    unfixed = []

    async with tpa_cm() as tpa:
        async for bar, event in tqdm_bar_async(
            await flatten_lists_async(
                [tpa.get_events_by_year(year=i) for i in range(1992, 2022)]
            )
        ):
            bar.set_description(event.key)
            if (event.lat, event.lng) == (0.0, 0.0):
                unfixed.append(event)

    print("")
    print(
        tabulate(
            [[e.key, e.city, e.state_prov, e.country] for e in unfixed],
            headers=["Key", "City", "State", "Country"],
        )
    )


@expose
async def dist(tkey, ekey):
    async with tpa_cm() as tpa:
        team = await tpa.get_team(team_key=tkey)
        event = await tpa.get_event(event_key=ekey)
        osrm.RequestConfig.host = "router.project-osrm.org"

        res = osrm.simple_route(
            [team.lng, team.lat], [event.lng, event.lat], geometry="wkt"
        )

        rt = res["routes"][0]
        dist = rt["distance"]
        dur = rt["duration"]

        print(f"{team.key} -> {event.key} should take ~{round(dur / 60)} mins")


@expose
async def tdist(tkey, tkey2):
    async with tpa_cm() as tpa:
        team = await tpa.get_team(team_key=tkey)
        team2 = await tpa.get_team(team_key=tkey2)

        osrm.RequestConfig.host = "router.project-osrm.org"

        res = osrm.simple_route(
            [team.lng, team.lat], [team2.lng, team2.lat], geometry="wkt"
        )

        rt = res["routes"][0]
        dur = rt["duration"]

        print(f"{team.key} -> {team2.key} should take ~{round(dur / 60)} mins")
