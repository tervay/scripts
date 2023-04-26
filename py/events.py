from collections import defaultdict
from itertools import combinations
from typing import List

import plotly.graph_objects as go
from grpclib.exceptions import GRPCError
from rich import print
from rich.pretty import pprint
from tqdm.rich import trange
from rich.table import Table
from protos.tpa import EliminationAlliance
from py.cli import expose
from tabulate import tabulate
from py.tba import AwardType, EventType
from py.tpa import tpa_cm
from py.util import (
    CURRENT_YEAR_RANGE,
    OPPOSITE_COLOR,
    all_events_with_bar,
    file_cm,
    find,
    get_savepath,
    make_table,
    make_table_from_dict,
    sort_matches,
    tqdm_bar,
)

import statbotics

# sb = statbotics.Statbotics()


@expose
async def event_info(key: str):
    async with tpa_cm() as tpa:
        pprint(await tpa.get_event(event_key=key))


def elim_perms(seeds, n, disallowed):
    perms = list(combinations(seeds, n))
    for d in disallowed:
        perms = list(filter(lambda p: not (d[0] in p and d[1] in p), perms))

    return list(perms)


def elim_str(alliances: List[EliminationAlliance], event_key: str) -> str:
    s = ""
    s += "1" if alliances[7].status.level == "qf" else "8"
    s += "2" if alliances[6].status.level == "qf" else "7"
    s += "3" if alliances[5].status.level == "qf" else "6"
    s += "4" if alliances[4].status.level == "qf" else "5"

    s = "".join([str(c) for c in sorted([int(c) for c in s])])

    s += "_"

    sf_s = []
    for i, a in enumerate(alliances, start=1):
        if a.status.level == "sf":
            for opp in {
                1: [4, 5],
                8: [4, 5],
                2: [3, 6],
                7: [3, 6],
                3: [2, 7],
                6: [2, 7],
                4: [1, 8],
                5: [1, 8],
            }[i]:
                if alliances[opp - 1].status.level == "f":
                    sf_s.append(opp)

    s += "".join([str(c) for c in sorted(sf_s)])

    s += "_"
    for i, a in enumerate(alliances, start=1):
        if a.status.status == "won":
            s += str(i)

    return s


@expose
async def bracket_counts():
    counts = {}
    qf_perms = elim_perms([1, 2, 3, 4, 5, 6, 7, 8], 4, [(1, 8), (2, 7), (3, 6), (4, 5)])
    for qfp in qf_perms:
        qfs = "".join([str(c) for c in sorted(qfp)])

        sf_perms = elim_perms(
            sorted(qfp),
            2,
            [
                (1, 4),
                (1, 5),
                (8, 4),
                (8, 5),
                (2, 3),
                (2, 6),
                (7, 3),
                (7, 6),
                (4, 1),
                (4, 8),
                (5, 1),
                (5, 8),
            ],
        )
        for sfp in sf_perms:
            sfs = "".join([str(c) for c in sorted(sfp)])

            f_perms = elim_perms(sorted(sfp), 1, [])

            for fp in f_perms:
                fs = "".join([str(c) for c in fp])
                bracket_str = f"{qfs}_{sfs}_{fs}"
                counts[bracket_str] = []

    async with tpa_cm() as tpa:
        skipped_lt_8 = []
        skipped_bad_data = []

        for bar, year in tqdm_bar(range(2010, 2021)):
            for event in [
                e
                async for e in tpa.get_events_by_year(year=year)
                if e.event_type in EventType.STANDARD_EVENT_TYPES
            ]:
                bar.set_description(event.key)
                a = [a async for a in tpa.get_event_alliances(event_key=event.key)]
                if len(a) != 8:
                    skipped_lt_8.append(event.key)
                    continue

                s = elim_str(
                    [a async for a in tpa.get_event_alliances(event_key=event.key)],
                    event.key,
                )
                if s not in counts:
                    skipped_bad_data.append(event.key)
                    continue

                counts[s].append(event.key)

    with file_cm(get_savepath("out.tsv"), "w+") as f:
        for bracket, events in sorted(counts.items(), key=lambda t: -len(t[1])):
            f.write(f"{bracket}\t{len(events)}\t{', '.join(events)}\n")

    print(f"{skipped_bad_data=}")
    print(f"{skipped_lt_8=}")

    n_counts = defaultdict(lambda: 0)
    for bracket, events in counts.items():
        n_counts[bracket[-1]] += len(events)

    print(n_counts)


@expose
async def test(key):
    async with tpa_cm() as tpa:
        print([ea async for ea in tpa.get_event_alliances(event_key=key)])


@expose
async def retention_2021():
    results = {}
    async with tpa_cm() as tpa:
        for bar, event in tqdm_bar(
            [
                e
                async for e in tpa.get_events_by_year(year=2020)
                if e.event_type in EventType.NON_CMP_EVENT_TYPES
            ]
        ):
            played_in_2021 = []
            bar.set_description(event.key)
            teams = [t async for t in tpa.get_event_teams(event_key=event.key)]
            if len(teams) == 0:
                continue

            for team in teams:
                team_events = [
                    e
                    async for e in tpa.get_team_events_by_year(
                        team_key=team.key, year=2021
                    )
                ]

                if len(team_events) > 1:
                    played_in_2021.append(team)

            results[event.key] = (len(played_in_2021), len(teams))

    with file_cm(get_savepath("out.csv"), "w+") as f:
        for e, (p2021, p2020) in sorted(
            results.items(), key=lambda t: -t[1][0] / t[1][1]
        ):
            print(f"{e},{p2020},{p2021},{p2021/p2020}", file=f)


@expose
async def biggest_chokes(year):
    out = []

    async with tpa_cm() as tpa:
        for bar, event in tqdm_bar(
            [
                e
                async for e in tpa.get_events_by_year(year=year)
                if e.event_type in EventType.NON_CMP_EVENT_TYPES
            ]
        ):
            bar.set_description(event.key)
            rankings = await tpa.get_event_rankings(event_key=event.key)
            if len(rankings.rankings) == 0:
                continue

            rp1 = rankings.rankings[0].sort_orders[0]
            rp2 = rankings.rankings[1].sort_orders[0]
            blowout_ratio = rp1 / rp2

            results = [a async for a in tpa.get_event_alliances(event_key=event.key)]
            results.sort(key=lambda ea: int(ea.name[-1]))

            if results[0].status.status != "won":
                out.append([event.key, rp1, rp2, blowout_ratio])

    out.sort(key=lambda r: r[-1])
    print(make_table(col_names=["Event Key", "1st", "2nd", "Ratio"], row_vals=out))


@expose
async def lowest_winners(year):
    out = []
    async with tpa_cm() as tpa:
        for bar, event in tqdm_bar(
            [
                e
                async for e in tpa.get_events_by_year(year=year)
                if e.event_type in EventType.NON_CMP_EVENT_TYPES
            ]
        ):
            bar.set_description(event.key)
            rankings = await tpa.get_event_rankings(event_key=event.key)
            if len(rankings.rankings) == 0:
                continue

            alliances = [a async for a in tpa.get_event_alliances(event_key=event.key)]
            winner = find(alliances, lambda a: a.status.status == "won")
            if winner is None:
                continue

            fp = winner.picks[1]
            fp_rank = find(rankings.rankings, lambda r: r.team_key == fp).rank

            out.append(
                [
                    event.short_name,
                    winner.name[-1],
                    winner.picks[0][3:],
                    fp[3:],
                    fp_rank,
                    len(rankings.rankings),
                ]
            )

    out.sort(key=lambda r: r[4])
    print(
        make_table(
            col_names=["Key", "Seed", "Captain", "First Pick", "FP Rank", "# Teams"],
            row_vals=out,
        )
    )

    for last in out[-2:][::-1]:
        print(
            f"{year}: {last[0]}; alliance {last[1]} captain {last[2]} first picks {last[3]} (rank {last[4]}/{last[5]})"
        )


@expose
async def lowest_winners2():
    out = []
    async with tpa_cm() as tpa:
        for year in range(2010, 2021):
            for bar, event in tqdm_bar(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    if e.event_type in EventType.NON_CMP_EVENT_TYPES
                ]
            ):
                bar.set_description(event.key)
                rankings = await tpa.get_event_rankings(event_key=event.key)
                if len(rankings.rankings) == 0:
                    continue

                alliances = [
                    a async for a in tpa.get_event_alliances(event_key=event.key)
                ]
                winner = find(alliances, lambda a: a.status.status == "won")
                if winner is None:
                    continue

                fp = winner.picks[1]
                fp_rank = find(rankings.rankings, lambda r: r.team_key == fp).rank

                out.append(
                    [
                        event.short_name,
                        winner.name[-1],
                        winner.picks[0][3:],
                        fp[3:],
                        fp_rank,
                        len(rankings.rankings),
                        event.year,
                        fp_rank / len(rankings.rankings),
                    ]
                )

    out.sort(key=lambda r: r[-1])
    print(
        make_table(
            col_names=["Key", "Seed", "Captain", "First Pick", "FP Rank", "# Teams"],
            row_vals=out,
        )
    )

    for last in out[-10:][::-1]:
        print(
            f"{last[-2]}: {last[0]}; alliance {last[1]} captain {last[2]} first picks {last[3]} (rank {last[4]}/{last[5]})"
        )


@expose
async def ranks_over_time(event_key: str):
    rp = defaultdict(lambda: 0)
    team_rp_history = defaultdict(list)
    averages = defaultdict(lambda: [0])
    async with tpa_cm() as tpa:
        teams = [t async for t in tpa.get_event_teams(event_key=event_key)]
        matches = [
            m
            async for m in tpa.get_event_matches(event_key=event_key)
            if m.comp_level == "qm"
        ]
        matches = sort_matches(matches)

        for match in matches:
            for tk in [
                tk
                for tk in match.alliances.blue.team_keys
                if tk
                not in (
                    match.alliances.blue.surrogate_team_keys
                    + match.alliances.blue.dq_team_keys
                )
            ]:
                team_rp_history[tk].append(match.blue_rp)

            for tk in [
                tk
                for tk in match.alliances.red.team_keys
                if tk
                not in (
                    match.alliances.red.surrogate_team_keys
                    + match.alliances.red.dq_team_keys
                )
            ]:
                team_rp_history[tk].append(match.red_rp)

            for tk in (
                match.alliances.blue.dq_team_keys + match.alliances.red.dq_team_keys
            ):
                team_rp_history[tk].append(0)

            for t in teams:
                if t.key not in team_rp_history:
                    team_rp_history[t.key].append(0)

            for tk, history in team_rp_history.items():
                averages[tk].append(round(sum(history) / len(history), 2))
                # averages[tk].append(sum(history))

    fig = go.Figure()

    for tk, averages in sorted(averages.items(), key=lambda t: int(t[0][3:])):
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(matches) + 1)),
                y=averages,
                mode="lines",
                name=tk,
            )
        )

    fig.update_layout(
        title=f"{event_key} RP avg over time",
        xaxis_title="Qual Match #",
        yaxis_title="RP Avg",
        legend_title="Teams",
    )
    fig.show()


@expose
async def compare_events(year_start: int, year_end: int, *ekeys):
    event_history = defaultdict(dict)
    async with tpa_cm() as tpa:
        for year in trange(year_start, year_end + 1):
            for ekey in ekeys:
                try:
                    event = await tpa.get_event(event_key=f"{year}{ekey}")
                except GRPCError:
                    continue

                event_teams = [
                    t async for t in tpa.get_event_teams(event_key=f"{year}{ekey}")
                ]
                event_elos = [t.yearly_elos[2019] for t in event_teams]
                event_elos.sort(reverse=True)
                num_teams = len(event_elos)
                top_quartile = int(round(num_teams / 4))
                event_history[ekey][year] = (
                    sum(event_elos[:top_quartile]) / top_quartile
                )

    fig = go.Figure()
    max_elo = 0
    for ekey, history in event_history.items():
        data = [(year, elo) for year, elo in history.items()]
        max_elo = max(max_elo, max(t[1] for t in data))
        data.sort(key=lambda t: t[0])
        fig.add_trace(
            go.Scatter(
                x=[t[0] for t in data],
                y=[t[1] for t in data],
                mode="lines",
                name=ekey,
            )
        )

    fig.update_yaxes(range=[1500, 1800])
    fig.update_layout(
        legend_title="Events",
        xaxis={"tickmode": "array", "tickvals": list(range(year_start, year_end + 1))},
    )
    fig.show()


@expose
async def division_buddies():
    count = defaultdict(lambda: 0)
    async with tpa_cm() as tpa:
        for year in range(2001, CURRENT_YEAR_RANGE):
            for bar, event in tqdm_bar(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    if e.event_type == EventType.CMP_DIVISION
                ]
            ):
                bar.set_description(event.key)
                teams = [t async for t in tpa.get_event_teams(event_key=event.key)]
                for t1 in teams:
                    for t2 in teams:
                        if t1.key == t2.key:
                            continue

                        combo = tuple(sorted([t1.team_number, t2.team_number]))
                        count[combo] += 0.5

    table = []
    for (t1, t2), c in sorted(count.items(), key=lambda t: -t[1])[:50]:
        table.append([t1, t2, c])

    print(make_table(["T1", "T2", "#"], table))


@expose
async def international(year: int):
    pcts = dict()
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=year,
            year_end=year,
            condition=lambda e: e.event_type in EventType.NON_CMP_EVENT_TYPES,
        ):
            total = 0
            intntl = 0
            async for team in tpa.get_event_teams(event_key=event.key):
                total += 1
                if team.country != event.country:
                    intntl += 1

            pcts[event.short_name] = round(100 * intntl / total, 2)

    print(
        make_table_from_dict(
            {k: v for k, v in pcts.items() if v != 0},
            col_names=["Event", "%"],
        )
    )


@expose
async def event_weaknesses():
    codes = [
        ["mabri"],
        ["rismi", "ripro"],
        ["marea"],
        ["nhgrs"],
        ["ctwat"],
        ["melew"],
        ["mawne"],
        ["mabos"],
        ["macma"],
        ["cthar"],
        ["mawor"],
        ["nhdur", "nhsea"],
    ]

    rows = []
    async with tpa_cm() as tpa:
        for code in codes:
            elos = [[], [], []]
            for subcode in code:
                for year in range(2016, 2023):
                    try:
                        data = sb.get_event(f"{year}{subcode}")
                        # elos.append(
                        #     [data["elo_mean"], data["elo_top24"], data["elo_top8"]]
                        # )

                        elos[0].append(data["elo_mean"])
                        elos[1].append(data["elo_top24"])
                        elos[2].append(data["elo_top8"])
                    except:
                        pass

            rows.append(
                [
                    subcode,
                    len(elos[0]),
                    round(sum(elos[0]) / len(elos[0])),
                    round(sum(elos[1]) / len(elos[1])),
                    round(sum(elos[2]) / len(elos[2])),
                ]
            )

    rows.sort(key=lambda r: r[-1])

    for row in rows:
        print(",".join([str(n) for n in row]))

    print(make_table(col_names=["Code", "#", "All", "Top24", "Top8"], row_vals=rows))


@expose
async def lost_qf1_won_event():
    out = []
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2016,
            year_end=2022,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                if award.award_type == AwardType.WINNER:
                    team_key = award.recipient_list[0].team_key
                    matches = sorted(
                        [
                            m
                            async for m in tpa.get_team_event_matches(
                                team_key=team_key, event_key=event.key
                            )
                            if m.comp_level == "qf"
                        ],
                        key=lambda m: m.match_number,
                    )

                    if len(matches) == 0:
                        continue

                    match = matches[0]
                    color_played = (
                        "red" if team_key in match.alliances.red.team_keys else "blue"
                    )
                    if match.winning_alliance != color_played:
                        alliance = "-".join(
                            [x.team_key[3:] for x in award.recipient_list]
                        )
                        out.append([event.key, alliance])

    pprint(out)
    print(len(out))


@expose
async def vods(team_number: int):
    async with tpa_cm() as tpa:
        async for event in tpa.get_team_events(team_key=f"frc{team_number}"):
            out = []
            for wc in event.webcasts:
                if wc.type == "twitch":
                    out.append(f"https://www.twitch.tv/{wc.channel}/videos")
                if wc.type == "youtube":
                    out.append(f"https://www.youtube.com/watch?v={wc.channel}")

            print(f'{event.start_date} - {event.key.rjust(4 + 6)} - {" / ".join(out)}')


@expose
async def triple_plays():
    out = []
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2000,
            year_end=2023,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            winners = []
            wffa = None
            impact = None
            async for award in tpa.get_event_awards(event_key=event.key):
                if award.award_type in AwardType.BLUE_BANNER_AWARDS:
                    if award.award_type == AwardType.WINNER:
                        winners = [r.team_key for r in award.recipient_list]
                    if award.award_type == AwardType.WOODIE_FLOWERS:
                        wffa = award.recipient_list[0].team_key
                    if award.award_type == AwardType.CHAIRMANS:
                        impact = award.recipient_list[0].team_key

            if wffa == impact and wffa in winners:
                out.append([wffa, event.key])

    print(tabulate(out, headers=["Team", "Event"], tablefmt="pipe"))


@expose
async def regions_by_einstein():
    counts = defaultdict(int)

    conv = {
        "Connecticut": "NE",
        "Massachusetts": "NE",
        "Maine": "NE",
        "Rhode Island": "NE",
        "Vermont": "NE",
        "New Hampshire": "NE",
        "New Jersey": "FMA",
        "Pennsylvania": "FMA",
        "Delaware": "FMA",
        "Virginia": "CHS",
        "Maryland": "CHS",
        "District of Columbia": "CHS",
        "Oregon": "PNW",
        "Washington": "PNW",
        "New Mexico": "FIT",
        "Texas": "FIT",
    }

    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2014,
            year_end=2023,
            condition=lambda e: e.event_type == EventType.CMP_FINALS,
        ):
            async for alliance in tpa.get_event_alliances(event_key=event.key):
                for tk in alliance.picks:
                    team = await tpa.get_team(team_key=tk)
                    if team.country == "USA":
                        counts[conv.get(team.state_prov, team.state_prov)] += 1
                    else:
                        counts[team.country] += 1

    pprint(sorted(counts.items(), key=lambda t: -t[1]))
