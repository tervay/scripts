from geopy.geocoders import Nominatim
from protos.tpa import AllTeamLocationCaches, LocationCache, TeamLocationCache
from tabulate import tabulate

from py.cli import expose, pprint
from py.tpa import tpa_cm
from py.util import (
    MAX_TEAMS_PAGE_NUM,
    file_cm,
    flatten_lists_async,
    get_savepath,
    tqdm_bar_async,
)


@expose
async def geocode_teams():
    nom = Nominatim(user_agent="frcscripts")
    full_cache = AllTeamLocationCaches()
    unfixed = []

    async with tpa_cm() as tpa:
        async for bar, team in tqdm_bar_async(
            await flatten_lists_async(
                [
                    tpa.get_teams_by_year(page_num=i, year=2021)
                    for i in range(MAX_TEAMS_PAGE_NUM)
                ]
            )
        ):
            bar.set_description(team.key)
            if 0 in [len(team.city), len(team.state_prov), len(team.country)]:
                continue

            if team.team_number in [5415]:
                unfixed.append(team)
                continue

            loc = nom.geocode(f"{team.city}, {team.state_prov}, {team.country}")

            if loc is None:
                unfixed.append(team)
                print(team.key, team.city, team.state_prov, team.country)
                continue

            full_cache.team_locations.append(
                TeamLocationCache(
                    team=team,
                    location=LocationCache(
                        latitude=loc.latitude, longitude=loc.longitude
                    ),
                )
            )

    print(
        tabulate(
            [(t.team_number, t.city, t.state_prov, t.country) for t in unfixed],
            headers=["Team", "City", "State", "Country"],
        )
    )

    with file_cm(get_savepath("team_location_cache.pb"), "wb+") as f:
        f.write(full_cache.SerializeToString())


@expose
def geocode_events():
    pass
