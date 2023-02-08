from collections import defaultdict
from pprint import pprint
from py.cli import expose
from tqdm import tqdm
from py.tpa.context_manager import tpa_cm

from py.util import CURRENT_YEAR, CURRENT_YEAR_RANGE, all_events_with_bar, file_cm


@expose
async def region_stats(district_key: str):
    with file_cm("data.csv", "w+") as f:
        async with tpa_cm() as tpa:
            team_loc_cache = {}
            async for team in tpa.get_all_teams():
                team_loc_cache[team.key] = (
                    team.city,
                    team.state_prov,
                    team.nickname.replace(",", "."),
                )

            worlds_teams = defaultdict(list)
            async for event in all_events_with_bar(
                tpa,
                year_start=1992,
                year_end=CURRENT_YEAR,
                condition=lambda e: e.event_type == 3,
            ):
                async for team in tpa.get_event_teams(event_key=event.key):
                    worlds_teams[event.year].append(team.key)

            for year in tqdm(range(1992, CURRENT_YEAR_RANGE)):
                if year == 2021:
                    continue

                async for ranking in tpa.get_district_rankings(
                    district_key=f"{year}{district_key}"
                ):
                    row = [
                        year,
                        ranking.rank,
                        ranking.point_total,
                        ranking.team_key[3:],
                        team_loc_cache[ranking.team_key][2],
                        team_loc_cache[ranking.team_key][0],
                        team_loc_cache[ranking.team_key][1],
                        ranking.team_key in worlds_teams[year],
                        ranking.rookie_bonus,
                    ]
                    if len(ranking.event_points) > 0:
                        row.extend(
                            [
                                ranking.event_points[0].qual_points,
                                ranking.event_points[0].alliance_points,
                                ranking.event_points[0].elim_points,
                                ranking.event_points[0].award_points,
                                ranking.event_points[0].total,
                            ]
                        )

                    if len(ranking.event_points) > 1:
                        row.extend(
                            [
                                ranking.event_points[1].qual_points,
                                ranking.event_points[1].alliance_points,
                                ranking.event_points[1].elim_points,
                                ranking.event_points[1].award_points,
                                ranking.event_points[1].total,
                            ]
                        )

                    if len(ranking.event_points) > 2:
                        row.extend(
                            [
                                ranking.event_points[2].qual_points,
                                ranking.event_points[2].alliance_points,
                                ranking.event_points[2].elim_points,
                                ranking.event_points[2].award_points,
                                ranking.event_points[2].total,
                            ]
                        )

                    f.write(",".join([str(x) for x in row]) + "\n")
