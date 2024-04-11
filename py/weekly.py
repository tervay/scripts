from collections import defaultdict
from datetime import datetime
from pprint import pprint
from statistics import median

from tabulate import tabulate

from protos.tpa import (
    MatchScoreBreakdown2023AllianceAutocommunity,
    MatchScoreBreakdown2023AllianceTeleopcommunity,
)
from py.cli import expose
from py.tba import AwardType, EventType
from py.tpa import tpa_cm
from py.util import (
    CURRENT_YEAR,
    MAX_TEAMS_PAGE_NUM,
    MAX_TEAMS_PAGE_RANGE,
    OPPOSITE_COLOR,
    _confidence,
    _confidence_bayes,
    all_events_with_bar,
    wilson_sort,
    bayes_sort,
)

import scipy.special as sc

formats = [
    "plain",
    "simple",
    "github",
    "grid",
    "simple_grid",
    "rounded_grid",
    "heavy_grid",
    "mixed_grid",
    "double_grid",
    "fancy_grid",
    "outline",
    "simple_outline",
    "rounded_outline",
    "heavy_outline",
    "mixed_outline",
    "double_outline",
    "fancy_outline",
    "pipe",
    "orgtbl",
    "asciidoc",
    "jira",
    "presto",
    "pretty",
    "psql",
    "rst",
    "mediawiki",
    "moinmoin",
    "youtrack",
    "html",
    "unsafehtml",
    "latex",
    "latex_raw",
    "latex_booktabs",
    "latex_longtable",
    "textile",
    "tsv",
]


def take_top_n(data, n, getter):
    ret = []
    i = 0
    for item in data:
        if i < n:
            ret.append(item)
            i += 1
        elif i == n:
            prev_val = getter(ret[-1])
            new_val = getter(item)
            if prev_val == new_val:
                ret.append(item)
            else:
                break

    return ret


@expose
async def generate():
    to_run = [
        # [undefeated, "Remaining Undefeated Teams", ["Team", "Record"]],
        # [most_matches_played, "Most Matches Played", ["Team", "Played"]],
        # [most_wins, "Most Wins", ["Team", "Wins"]],
        # [winners_by_seed, "Winning Alliances by Seed", ["Name", "Count"]],
        [
            best_record,
            "Best Record (via confidence interval)",
            ["Team", "Record", "%", "Confidence"],
        ],
        # [
        #     best_record_2,
        #     "Best Record 2 (via Bayesian)",
        #     ["Team", "Record", "%", "Confidence"],
        # ],
        # [
        #     highest_score_minus_fouls,
        #     "Highest Score Minus Fouls",
        #     ["Week", "Match", "Teams", "Score"],
        # ],
        # [
        #     high_scores_by_district,
        #     "Highest Score Minus Fouls Per District",
        #     ["District", "Week", "Match", "Teams", "Score"],
        # ],
        [
            high_scores_by_region,
            "Highest Score Minus Fouls Per Region",
            ["Region", "Week", "Match", "Teams", "Score"],
        ],
        [
            median_scores_by_region,
            "Median Score Minus Fouls Per Region",
            ["Region", "Events", "Score"],
        ],
        # [
        #     highest_combined_score_minus_fouls,
        #     "Highest Combined Score Minus Fouls",
        #     ["Week", "Match", "Red", "Blue", "Red Pts", "Blue Pts", "Total"],
        # ],
        # [highest_auto, "Highest Auto", ["Week", "Match", "Teams", "Score"]],
        # [
        #     fastest_median_match_turnaround,
        #     "Fastest Median Match Turnaround Time",
        #     ["Week", "Event", "Median Turnaround Mins"],
        # ],
        # [
        #     slowest_median_match_turnaround,
        #     "Slowest Median Match Turnaround Time",
        #     ["Week", "Event", "Median Turnaround Mins"],
        # ],
        # [
        #     most_filled_community,
        #     "Most Filled Community",
        #     ["Week", "Match", "Teams", "Count/27"],
        # ],
        [
            highest_median_match_score,
            "Highest Median Match Score (w/o fouls)",
            ["Week", "Event", "Median Score"],
        ],
        [most_awards, "Most Awards", ["Team", "Awards"]],
        # [most_banners, "Most Banners", ["Team", "Banners"]],
        # [most_district_pts, "Most District Points", ["Team", "E1", "E2", "Total"]],
        # [most_filled_grids, "Most Filled Grids", ["Team", "Count"]],
        # [filled_grids, "Filled Grids", ["Week", "Match", "Time", "Teams"]],
        [most_notes_scored, "Most Total Notes", ["Key", "Teams", "Count"]],
        [most_teleop_notes_scored, "Most Teleop Notes", ["Key", "Teams", "Count"]],
    ]
    # await summary()
    with open("out.md", "w+") as f:
        for i, (table_fn, title, headers) in enumerate(to_run, start=1):
            print(f"{i} / {len(to_run)} - {title}")
            data = await table_fn()
            ranked = [[i] + row for (i, row) in enumerate(data, start=1)]
            print(f"### {title}\n", file=f)
            print(tabulate(ranked, headers=["N"] + headers, tablefmt="pipe"), file=f)
            print("\n", file=f)
            f.flush()


@expose
async def summary():
    played = set()
    unplayed = set()
    events = defaultdict(set)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for team in tpa.get_event_teams(event_key=event.key):
                unplayed.add(team.key)

            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    for tk in getattr(match.alliances, c).team_keys:
                        played.add(tk)
                        events[tk].add(match.event_key)

    print(
        f"{len(played)} teams have played. {len(unplayed.difference(played))} are yet to play."
    )

    for n in [1, 2, 3, 4, 5, 6]:
        count = list(filter(lambda t: len(t[1]) == n, events.items()))
        if len(count) == 0:
            continue
        if len(count) <= 5:
            print(
                f"{', '.join([str(x) for x in sorted([int(t[0][3:]) for t in count])])} have played {n} events."
            )
        else:
            print(f"{len(count)} have played {n} events.")


@expose
async def undefeated():
    wins = defaultdict(int)
    losses = defaultdict(int)
    ties = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if match.winning_alliance in ["red", "blue"]:
                    for tk in getattr(
                        match.alliances, match.winning_alliance
                    ).team_keys:
                        wins[tk] += 1
                    for tk in getattr(
                        match.alliances, OPPOSITE_COLOR[match.winning_alliance]
                    ).team_keys:
                        losses[tk] += 1
                else:
                    for c in ["red", "blue"]:
                        for tk in getattr(match.alliances, c).team_keys:
                            ties[tk] += 1

    data = []
    for t, w in sorted(wins.items(), key=lambda t: -t[1]):
        if losses[t] == 0:
            data.append([t[3:], f"{w}-0-{ties[t]}"])

    return data


@expose
async def most_matches_played():
    played = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            # condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
            condition=lambda e: True,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    for tk in getattr(match.alliances, c).team_keys:
                        played[tk] += 1

    data = []
    skips = {f"frc{t}" for t in range(9900, 10000)}
    for t, p in sorted(played.items(), key=lambda t: -t[1]):
        if t not in skips:
            data.append([t[3:], p])

    return take_top_n(data, 10, getter=lambda row: row[1])


async def most_wins():
    wins = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            # condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
            condition=lambda e: True,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue
                if match.winning_alliance is None or match.winning_alliance == "":
                    continue

                for tk in getattr(match.alliances, match.winning_alliance).team_keys:
                    wins[tk] += 1

    data = []
    skips = {f"frc{t}" for t in range(9900, 10000)}
    for t, p in sorted(wins.items(), key=lambda t: -t[1]):
        if t not in skips:
            data.append([t[3:], p])

    return take_top_n(data, 10, getter=lambda row: row[1])


@expose
async def best_record():
    z = 2
    records = defaultdict(lambda: {"w": 0, "l": 0, "t": 0})
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
            # condition=lambda e: True,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if match.winning_alliance in ["red", "blue"]:
                    for tk in getattr(
                        match.alliances, match.winning_alliance
                    ).team_keys:
                        records[tk]["w"] += 1
                    for tk in getattr(
                        match.alliances, OPPOSITE_COLOR[match.winning_alliance]
                    ).team_keys:
                        records[tk]["l"] += 1
                else:
                    for c in ["red", "blue"]:
                        for tk in getattr(match.alliances, c).team_keys:
                            records[tk]["t"] += 1

    data = []
    skips = {f"frc{t}" for t in range(9900, 10000)}
    for t, record in wilson_sort(
        records.items(),
        positive=lambda d: d[1]["w"],
        negative=lambda d: d[1]["l"] + d[1]["t"],
        z=z,
    ):
        if t not in skips:
            data.append(
                [
                    t[3:],
                    (
                        f'{record["w"]}-{record["l"]}-{record["t"]}'
                        if record["t"] > 0
                        else f'{record["w"]}-{record["l"]}'
                    ),
                    round(100 * record["w"] / sum(record.values()), 1),
                    round(
                        _confidence(
                            ups=record["w"], downs=record["l"] + record["t"], z=z
                        ),
                        3,
                    ),
                ]
            )

    return take_top_n(data, 50, lambda t: t[-1])


@expose
async def best_record_2():
    L = 5
    records = defaultdict(lambda: {"w": 0, "l": 0, "t": 0})
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
            # condition=lambda e: True,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if match.winning_alliance in ["red", "blue"]:
                    for tk in getattr(
                        match.alliances, match.winning_alliance
                    ).team_keys:
                        records[tk]["w"] += 1
                    for tk in getattr(
                        match.alliances, OPPOSITE_COLOR[match.winning_alliance]
                    ).team_keys:
                        records[tk]["l"] += 1
                else:
                    for c in ["red", "blue"]:
                        for tk in getattr(match.alliances, c).team_keys:
                            records[tk]["t"] += 1

    data = []
    skips = {f"frc{t}" for t in range(9900, 10000)}
    for t, record in bayes_sort(
        records.items(),
        positive=lambda d: d[1]["w"],
        negative=lambda d: d[1]["l"] + d[1]["t"],
        L=L,
    ):
        if t not in skips:
            data.append(
                [
                    t[3:],
                    (
                        f'{record["w"]}-{record["l"]}-{record["t"]}'
                        if record["t"] > 0
                        else f'{record["w"]}-{record["l"]}'
                    ),
                    round(100 * record["w"] / sum(record.values()), 1),
                    round(
                        _confidence_bayes(
                            ups=record["w"],
                            downs=record["l"] + record["t"],
                            L=L,
                        ),
                        3,
                    ),
                ]
            )

    return take_top_n(data, 50, lambda t: t[-1])


@expose
async def highest_auto():
    pts = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    pts[
                        (
                            event.week + 1,
                            match.key,
                            "-".join(
                                [k[3:] for k in getattr(match.alliances, c).team_keys]
                            ),
                        )
                    ] = getattr(match.score_breakdown_2023, c).auto_points

    data = []
    for t, p in sorted(pts.items(), key=lambda t: -t[1]):
        data.append([t[0], t[1], t[2], p])

    return take_top_n(data, 10, lambda t: -t[-1])


@expose
async def highest_score_minus_fouls():
    pts = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    pts[
                        (
                            event.week + 1,
                            match.key,
                            "-".join(
                                [k[3:] for k in getattr(match.alliances, c).team_keys]
                            ),
                        )
                    ] = (
                        getattr(match.score_breakdown_2023, c).total_points
                        - getattr(match.score_breakdown_2023, c).foul_points
                    )

    data = []
    for t, p in sorted(pts.items(), key=lambda t: -t[1]):
        data.append([t[0], t[1], t[2], p])

    return take_top_n(data, 10, lambda t: -t[-1])


@expose
async def highest_combined_score_minus_fouls():
    pts = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                pts[
                    (
                        event.week + 1,
                        match.key,
                        "-".join([k[3:] for k in match.alliances.red.team_keys]),
                        "-".join([k[3:] for k in match.alliances.blue.team_keys]),
                    )
                ] = [
                    match.score_breakdown_2023.red.total_points
                    - match.score_breakdown_2023.red.foul_points,
                    match.score_breakdown_2023.blue.total_points
                    - match.score_breakdown_2023.blue.foul_points,
                ]

    data = []
    for t, p in sorted(pts.items(), key=lambda t: -sum(t[1])):
        data.append([t[0], t[1], t[2], t[3], p[0], p[1], sum(p)])

    return take_top_n(data, 10, lambda t: -t[-1])


@expose
async def fastest_median_match_turnaround():
    medians = {}
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            if event.key == "2023gaalb":
                continue

            turnarounds = []
            last_time = None
            try:
                async for match in tpa.get_event_matches(event_key=event.key):
                    if (
                        match.alliances.blue.score == -1
                        and match.alliances.red.score == -1
                    ):
                        continue

                    if last_time is None:
                        last_time = match.actual_time
                        continue

                    turnarounds.append(match.actual_time - last_time)
                    last_time = match.actual_time
            except:
                continue

            if len(turnarounds) == 0:
                continue

            medians[(event.week + 1, event.key)] = median(turnarounds)

    data = []
    for t, p in sorted(medians.items(), key=lambda t: t[1]):
        data.append([t[0], t[1], round(p / 60, 2)])

    return take_top_n(data, 200, lambda t: -t[-1])


@expose
async def slowest_median_match_turnaround():
    medians = {}
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            turnarounds = []
            last_time = None
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if last_time == None:
                    last_time = match.actual_time
                    continue

                turnarounds.append(match.actual_time - last_time)
                last_time = match.actual_time

            if len(turnarounds) == 0:
                continue

            medians[(event.week + 1, event.key)] = median(turnarounds)

    data = []
    for t, p in sorted(medians.items(), key=lambda t: -t[1]):
        data.append([t[0], t[1], round(p / 60, 2)])

    return take_top_n(data, 10, lambda t: -t[-1])


@expose
async def most_filled_community():
    pts = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            if event.key == "2023gaalb":
                continue

            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    bot = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.b.count("None")
                    mid = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.m.count("None")
                    top = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.t.count("None")

                    pts[
                        (
                            event.week + 1,
                            match.key,
                            "-".join(
                                [k[3:] for k in getattr(match.alliances, c).team_keys]
                            ),
                        )
                    ] = (
                        bot + mid + top
                    )

    data = []
    for t, p in sorted(pts.items(), key=lambda t: -t[1]):
        data.append([t[0], t[1], t[2], p])

    return take_top_n(data, 15, lambda t: -t[-1])


@expose
async def filled_grids():
    filled = []
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: True,
        ):
            if event.key == "2023gaalb":
                continue

            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if not hasattr(match, "score_breakdown_2023"):
                    continue

                for c in ["red", "blue"]:
                    bot = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.b.count("None")
                    mid = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.m.count("None")
                    top = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.t.count("None")

                    if bot + mid + top == 27:
                        filled.append(
                            [
                                event.week + 1,
                                match.key,
                                match.actual_time,
                                "-".join(
                                    [
                                        k[3:]
                                        for k in getattr(match.alliances, c).team_keys
                                    ]
                                ),
                            ]
                        )

    def fmt_time(timestamp):
        return datetime.utcfromtimestamp(timestamp).strftime("%b %-d %H:%M:%S %Z")

    data = []
    for t in sorted(filled, key=lambda t: t[2]):
        data.append([t[0], t[1], fmt_time(t[2]), t[3]])

    return data


@expose
async def most_filled_grids():
    counts = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: True,
        ):
            if event.key == "2023gaalb":
                continue

            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if not hasattr(match, "score_breakdown_2023"):
                    continue

                for c in ["red", "blue"]:
                    bot = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.b.count("None")
                    mid = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.m.count("None")
                    top = 9 - getattr(
                        match.score_breakdown_2023, c
                    ).teleop_community.t.count("None")

                    if bot + mid + top == 27:
                        for team in getattr(match.alliances, c).team_keys:
                            counts[int(team[3:])] += 1

    def fmt_time(timestamp):
        return datetime.utcfromtimestamp(timestamp).strftime("%b %-d %H:%M:%S %Z")

    data = []
    for t in sorted(counts.items(), key=lambda t: -t[1]):
        data.append([t[0], t[1]])

    return take_top_n(data, 5, getter=lambda r: r[1])


@expose
async def highest_median_match_score():
    medians = {}
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            scores = []
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                scores.append(
                    match.score_breakdown_2024.blue.total_points
                    - match.score_breakdown_2024.blue.foul_points
                )
                scores.append(
                    match.score_breakdown_2024.red.total_points
                    - match.score_breakdown_2024.red.foul_points
                )

            if len(scores) == 0:
                continue

            medians[(event.week + 1, event.key)] = median(scores)

    data = []
    for t, p in sorted(medians.items(), key=lambda t: -t[-1]):
        data.append([t[0], t[1], p])

    return take_top_n(data, 200, lambda t: -t[-1])


@expose
async def most_awards():
    count = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                for recipient in award.recipient_list:
                    if recipient.team_key is not None and len(recipient.team_key) > 0:
                        count[recipient.team_key] += 1

    data = []
    for t, p in sorted(count.items(), key=lambda t: -t[-1]):
        data.append([t[3:], p])

    return take_top_n(data, 10, lambda t: -t[-1])


@expose
async def most_banners():
    count = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                if award.award_type in AwardType.BLUE_BANNER_AWARDS:
                    for recipient in award.recipient_list:
                        if recipient.team_key is not None:
                            count[recipient.team_key] += 1

    data = []
    for t, p in sorted(count.items(), key=lambda t: -t[-1]):
        data.append([t[3:], p])

    return take_top_n(data, 10, lambda t: -t[-1])


@expose
async def most_district_pts():
    events = defaultdict(list)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            dpts = await tpa.get_event_district_points(event_key=event.key)
            for tk, dp in dpts.points.items():
                if len(events[tk]) >= 2:
                    continue
                else:
                    events[tk].append(dp.total)

    data = []
    for t, p in sorted(events.items(), key=lambda t: -sum(t[1])):
        if len(p) == 1:
            data.append([t[3:], p[0], "-", sum(p)])
        else:
            data.append([t[3:], p[0], p[1], sum(p)])

    return take_top_n(data, 10, lambda t: t[-1])


async def high_scores_by_district():
    pts = defaultdict(lambda: defaultdict(int))
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES
            and e.district is not None
            and e.district != "",
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    pts[event.district.display_name][
                        (
                            event.week + 1,
                            match.key,
                            "-".join(
                                [k[3:] for k in getattr(match.alliances, c).team_keys]
                            ),
                        )
                    ] = (
                        getattr(match.score_breakdown_2024, c).total_points
                        - getattr(match.score_breakdown_2024, c).foul_points
                    )

    data = []
    for district, scores in pts.items():
        scores_ = sorted(scores.items(), key=lambda t: -t[1])
        (wk, key, teams), score = scores_[0]
        data.append([district, wk, key, teams, score])

    return sorted(data, key=lambda r: -r[-1])


@expose
async def high_scores_by_region():
    pts = defaultdict(lambda: defaultdict(int))
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            region = event.district.display_name
            if event.district.display_name == "":
                if event.country not in ["USA", "Canada"]:
                    region = event.country
                else:
                    region = event.state_prov

            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    pts[region][
                        (
                            event.week + 1,
                            match.key,
                            "-".join(
                                [k[3:] for k in getattr(match.alliances, c).team_keys]
                            ),
                        )
                    ] = (
                        getattr(match.score_breakdown_2024, c).total_points
                        - getattr(match.score_breakdown_2024, c).foul_points
                    )

    data = []
    for district, scores in pts.items():
        scores_ = sorted(scores.items(), key=lambda t: -t[1])
        (wk, key, teams), score = scores_[0]
        data.append([district, wk, key, teams, score])

    return sorted(data, key=lambda r: -r[-1])


@expose
async def median_scores_by_region():
    pts = defaultdict(list)
    event_counts = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            region = event.district.display_name
            if event.district.display_name == "":
                if event.country not in ["USA", "Canada"]:
                    region = event.country
                else:
                    region = event.state_prov

            event_counts[region] += 1

            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                for c in ["red", "blue"]:
                    pts[region].append(
                        (
                            getattr(match.score_breakdown_2024, c).total_points
                            - getattr(match.score_breakdown_2024, c).foul_points
                        )
                    )

    data = []
    for district, scores in pts.items():
        data.append([district, event_counts[district], median(scores)])

    return sorted(data, key=lambda r: -r[-1])


@expose
async def ma():
    async with tpa_cm() as tpa:
        async for team in tpa.get_all_teams():
            if team.state_prov.lower() in ["ma", "massachusetts"]:
                yrs = [
                    y.int_value
                    async for y in tpa.get_team_years_participated(team_key=team.key)
                ]
                if len(yrs) == 0:
                    continue

                print(
                    f"{team.team_number},{team.nickname},{sorted(yrs)[-1]},{team.city}"
                )


async def winners_by_seed():
    counts = defaultdict(lambda: 0)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for alliance in tpa.get_event_alliances(event_key=event.key):
                if alliance.status.status == "won":
                    counts[alliance.name] += 1
                    break

    data = []
    for a, count in counts.items():
        data.append([a, count])

    data.sort(key=lambda t: int(t[0][-1]))

    return take_top_n(data, 25, getter=lambda row: row[1])


async def most_notes_scored():
    results = []
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if not hasattr(match, "score_breakdown_2024"):
                    continue

                for c in ["red", "blue"]:
                    results.append(
                        [
                            match.key,
                            "-".join(
                                [(k[3:]) for k in getattr(match.alliances, c).team_keys]
                            ),
                            sum(
                                [
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).auto_amp_note_count,
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).teleop_amp_note_count,
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).auto_speaker_note_count,
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).teleop_speaker_note_count,
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).teleop_speaker_note_amplified_count,
                                ]
                            ),
                        ]
                    )

        results.sort(key=lambda t: -t[-1])

    return results[:25]


async def most_teleop_notes_scored():
    results = []
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=CURRENT_YEAR,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for match in tpa.get_event_matches(event_key=event.key):
                if match.alliances.blue.score == -1 and match.alliances.red.score == -1:
                    continue

                if not hasattr(match, "score_breakdown_2024"):
                    continue

                for c in ["red", "blue"]:
                    results.append(
                        [
                            match.key,
                            "-".join(
                                [(k[3:]) for k in getattr(match.alliances, c).team_keys]
                            ),
                            sum(
                                [
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).teleop_amp_note_count,
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).teleop_speaker_note_count,
                                    getattr(
                                        match.score_breakdown_2024, c
                                    ).teleop_speaker_note_amplified_count,
                                ]
                            ),
                        ]
                    )

        results.sort(key=lambda t: -t[-1])

    return results[:25]
