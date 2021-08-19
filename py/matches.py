from collections import defaultdict
from itertools import combinations

from rich import print

from protos.tpa import WltRecord
from py.cli import expose
from py.tba import EventType
from py.tpa import tpa_cm
from py.util import CURRENT_YEAR_RANGE, make_table, tqdm_bar, wilson_sort


def sort_combo(combination):
    combination = [str(c)[3:].strip("ABCDEFGHabcdefgh") for c in combination]
    try:
        return tuple(sorted(int(k) for k in combination))
    except ValueError:
        return tuple(combination)


@expose
async def teamups():
    records = defaultdict(lambda: WltRecord())

    async with tpa_cm() as tpa:
        for year in range(2006, CURRENT_YEAR_RANGE):
            for bar, event in tqdm_bar(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    if e.event_type in EventType.SEASON_EVENT_TYPES
                ]
            ):
                bar.set_description(event.key)
                async for match in tpa.get_event_matches(event_key=event.key):
                    for alliance in match.alliances.tied:
                        for combo in combinations(alliance.team_keys, 2):
                            combo = sort_combo(combo)
                            records[combo].ties += 1

                    if match.winning_alliance == "":
                        continue

                    for combo in combinations(match.alliances.winner.team_keys, 2):
                        combo = sort_combo(combo)
                        records[combo].wins += 1
                    for combo in combinations(match.alliances.loser.team_keys, 2):
                        combo = sort_combo(combo)
                        records[combo].losses += 1

    table = []
    for combo, record in wilson_sort(
        records.items(),
        positive=lambda t: t[1].wins,
        negative=lambda t: t[1].ties + t[1].losses,
        z=1.0,
        minimum_total=15,
    )[:75]:
        table.append(
            list(combo)
            + [
                record.wins,
                record.losses,
                record.ties,
                round(
                    record.wins / (record.wins + record.losses + record.ties) * 100, 2
                ),
            ]
        )

    print(make_table(["T1", "T2", "W", "L", "T", "%"], table))


@expose
async def check_teamups(t1: int, include_offseasons: bool = False):
    records = defaultdict(lambda: WltRecord())
    async with tpa_cm() as tpa:
        team1 = await tpa.get_team(team_key=f"frc{t1}")
        for year in range(team1.rookie_year, CURRENT_YEAR_RANGE):
            for bar, match in tqdm_bar(
                [
                    m
                    async for m in tpa.get_team_matches_by_year(
                        team_key=team1.key, year=year
                    )
                ]
            ):
                bar.set_description(match.event_key)
                if (
                    (await tpa.get_event(event_key=match.event_key)).event_type
                    not in EventType.SEASON_EVENT_TYPES
                ) and not include_offseasons:
                    continue

                if team1.key not in (
                    match.alliances.red.team_keys + match.alliances.blue.team_keys
                ):
                    continue

                for alliance in match.alliances.tied:
                    for combo in combinations(alliance.team_keys, 2):
                        combo = sort_combo(combo)
                        records[combo].ties += 1

                if match.winning_alliance == "":
                    continue

                for combo in combinations(match.alliances.winner.team_keys, 2):
                    combo = sort_combo(combo)
                    records[combo].wins += 1
                for combo in combinations(match.alliances.loser.team_keys, 2):
                    combo = sort_combo(combo)
                    records[combo].losses += 1

    for combo in records.copy().keys():
        if t1 not in combo:
            del records[combo]

    table = []
    for combo, record in wilson_sort(
        records.items(),
        positive=lambda t: t[1].wins,
        negative=lambda t: t[1].ties + t[1].losses,
        z=1.96,
    )[:20]:
        table.append(
            list(combo)
            + [
                record.wins,
                record.losses,
                record.ties,
                round(
                    record.wins / (record.wins + record.losses + record.ties) * 100, 2
                ),
            ]
        )

    print(make_table(["T1", "T2", "W", "L", "T", "%"], table))
