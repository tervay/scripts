from collections import defaultdict
from itertools import combinations
from pprint import pprint

from rich import print

from protos.tpa import WltRecord
from py.cli import expose
from py.tba import EventType
from py.tpa import tpa_cm
from py.util import (
    CURRENT_YEAR_RANGE,
    _confidence,
    all_events_with_bar,
    make_table,
    tqdm_bar,
    wilson_sort,
)


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


@expose
async def iri_indiana():
    d = defaultdict(lambda: 0)
    async with tpa_cm() as tpa:
        async for match in tpa.get_event_matches(event_key="2022iri"):
            for team in match.alliances.red.team_keys + match.alliances.blue.team_keys:
                t = await tpa.get_team(team_key=team)
                if t.state_prov == "Indiana":
                    d[match.key] += 1

    pprint(sorted(d.items(), key=lambda t: -t[1]))


@expose
async def most_matches(
    year: int, include_offseason: bool = True, include_b_bots: bool = True
):
    d = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0})
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=year,
            year_end=year,
            condition=lambda e: (
                e.event_type in EventType.SEASON_EVENT_TYPES
                if not include_offseason
                else True
            ),
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.key.startswith("2022mirr_ef"):
                    continue
                if [match.alliances.red.score, match.alliances.blue.score] == [-1, -1]:
                    continue

                for c in ["red", "blue"]:
                    for tk in getattr(match.alliances, c).team_keys:
                        if include_b_bots:
                            if tk[-1].lower() in ["a", "b", "c", "d"]:
                                tk = tk[:-1]

                        try:
                            if int(tk[3:]) > 9500:
                                continue
                        except:
                            pass

                        if match.winning_alliance == c:
                            d[tk]["wins"] += 1
                        elif match.alliances.red.score == match.alliances.blue.score:
                            d[tk]["ties"] += 1
                        else:
                            d[tk]["losses"] += 1

        rows = [
            [
                k[3:],
                v["wins"],
                v["losses"],
                v["ties"],
                str(round(v["wins"] * 100.0 / sum(list(v.values())), 1)) + "%",
                sum(list(v.values())),
            ]
            for (k, v) in d.items()
        ]

        top_n = 25

        print(
            make_table(
                col_names=["#", "Team", "W", "L", "T", "%", "Tot"],
                row_vals=[
                    [i] + r
                    for i, r in enumerate(
                        sorted(rows, key=lambda r: -r[-1])[:top_n], start=1
                    )
                ],
            )
        )

        print(
            make_table(
                col_names=["#", "Team", "W", "L", "T", "%", "Tot"],
                row_vals=[
                    [i] + r
                    for i, r in enumerate(
                        sorted(rows, key=lambda r: -r[1])[:top_n], start=1
                    )
                ],
            )
        )

        print(
            make_table(
                col_names=["#", "Team", "W", "L", "T", "%", "Tot"],
                row_vals=[
                    [i] + r
                    for i, r in enumerate(
                        wilson_sort(
                            rows,
                            positive=lambda r: r[1],
                            negative=lambda r: r[2] + r[3],
                            z=1.96,
                        )[:top_n],
                        start=1,
                    )
                ],
            )
        )


@expose
async def most_dominant(include_offseason: bool = False):
    d = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0})
    async with tpa_cm() as tpa:
        for year in range(2006, 2023):
            if year in [2020, 2021]:
                continue

            async for event in all_events_with_bar(
                tpa,
                year_start=year,
                year_end=year,
                condition=lambda e: (
                    e.event_type in EventType.SEASON_EVENT_TYPES
                    if not include_offseason
                    else True
                ),
            ):
                async for match in tpa.get_event_matches(event_key=event.key):
                    if match.key.startswith("2022mirr_ef"):
                        continue

                    for c in ["red", "blue"]:
                        for tk in getattr(match.alliances, c).team_keys:
                            if tk[-1].lower() in ["a", "b", "c", "d"]:
                                tk = tk[:-1]

                            try:
                                if int(tk[3:]) > 9000:
                                    continue
                            except:
                                pass

                            tk = f"{tk} {year}"

                            if match.winning_alliance == c:
                                d[tk]["wins"] += 1
                            elif (
                                match.alliances.red.score == match.alliances.blue.score
                            ):
                                d[tk]["ties"] += 1
                            else:
                                d[tk]["losses"] += 1
        rows = [
            [
                k[3:],
                v["wins"],
                v["losses"],
                v["ties"],
                str(round(v["wins"] * 100.0 / sum(list(v.values())), 1)) + "%",
                sum(list(v.values())),
            ]
            for (k, v) in d.items()
        ]

        print(
            make_table(
                col_names=["#", "Team", "W", "L", "T", "%", "Tot"],
                row_vals=[
                    [i] + r
                    for i, r in enumerate(
                        wilson_sort(
                            rows,
                            positive=lambda r: r[1],
                            negative=lambda r: r[2] + r[3],
                            z=1.96,
                        )[:1000],
                        start=1,
                    )
                ],
            )
        )


@expose
async def most_matches_fast():
    c = defaultdict(lambda: defaultdict(lambda: 0))
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa, year_start=2000, year_end=2021, condition=lambda e: True
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.key.startswith("2022mirr_ef"):
                    continue

                for tk in (
                    match.alliances.red.team_keys + match.alliances.blue.team_keys
                ):
                    try:
                        n = int(tk[3:])
                    except ValueError:
                        continue

                    if n > 9500:
                        continue

                    c[event.year][tk] += 1

    l = []

    for year, matches in c.items():
        for tk, count in matches.items():
            l.append((year, tk, count))

    l.sort(key=lambda t: -t[2])

    for i, blob in enumerate(l[:50], start=1):
        year, key, count = blob

        print(f"{str(i).rjust(2)}. {key[3:].rjust(4)} {year} - {str(count).rjust(3)}")

    l.sort(key=lambda t: (t[0], -t[2]))

    with open("out.txt", "w+") as f:
        for i, blob in enumerate(l, start=1):
            year, key, count = blob

            print(
                f"{str(i).rjust(4)}. {key[3:].rjust(4)} {year} - {str(count).rjust(3)}",
                file=f,
            )


@expose
async def most_cargo():
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2022,
            year_end=2022,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                pass
