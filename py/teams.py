from itertools import combinations
import json
import re
import statistics
from collections import defaultdict, Counter
from typing import Optional, List

import pandas as pd
import plotly.graph_objects as go
from rich import print
from rich.pretty import pprint
from tqdm.asyncio import tqdm
from tqdm.rich import tqdm as tqdm_sync
from tqdm.rich import trange
from protos.tpa import Color, WltRecord, Team
from py.cli import expose
from py.matches import sort_combo
from py.tba import AwardType, EventType, tba
from py.tpa import tpa_cm
from py.util import (
    CURRENT_YEAR,
    CURRENT_YEAR_RANGE,
    MAX_TEAMS_PAGE_NUM,
    MAX_TEAMS_PAGE_RANGE,
    OPPOSITE_COLOR,
    all_events_with_bar,
    all_teams_with_bar,
    file_cm,
    filter_completed_events,
    flatten_lists,
    flatten_lists_async,
    get_savepath,
    is_official_event,
    make_table,
    tqdm_bar,
    tqdm_bar_async,
    wilson_sort,
)


@expose
async def about(num):
    async with tpa_cm() as tpa:
        pprint(await tpa.get_team(team_key=f"frc{num}"))


@expose
def dlf_wffa():
    events = flatten_lists([tba.events(year=y) for y in range(2008, 2022)])
    events = filter_completed_events(events)

    dlf = {}
    wffa = {}

    for event in tqdm_sync(events):
        awards = tba.event_awards(event=event["key"])
        for award in awards:
            if award["award_type"] == 4:
                for recipient in award["recipient_list"]:
                    dlf[recipient["awardee"]] = (event["key"], recipient["team_key"])

            if award["award_type"] == 3:
                for recipient in award["recipient_list"]:
                    wffa[recipient["awardee"]] = (event["key"], recipient["team_key"])

    print(set(dlf.keys()) & set(wffa.keys()))


@expose
async def async_dlf_wffa():
    dlf, wffa = {}, {}
    async with tpa_cm() as tpa:
        async for event in tqdm(
            await flatten_lists_async(
                [tpa.get_events_by_year(year=y) for y in range(2008, 2022)]
            )
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                m = {4: dlf, 3: wffa}
                if award.award_type in m:
                    for recipient in award.recipient_list:
                        m[award.award_type][recipient.awardee] = (
                            event.key,
                            recipient.team_key,
                        )

    print(set(dlf.keys()) & set(wffa.keys()))


@expose
async def test(n):
    async with tpa_cm() as tpa:
        async for t in tpa.get_teams(page_num=n):
            print(t)


@expose
async def total(year: int = 2023):
    async with tpa_cm() as tpa:
        teams = [t async for t in tpa.get_all_teams_by_year(year=year)]
        print(len(teams))


@expose
async def costs(year):
    async with tpa_cm() as tpa:
        data = []
        wtf = []
        costs_by_states = defaultdict(list)

        async for bar, team in tqdm_bar_async(
            await flatten_lists_async(
                [
                    tpa.get_teams_by_year(year=year, page_num=i)
                    for i in range(MAX_TEAMS_PAGE_NUM)
                ]
            )
        ):
            bar.set_description(team.key)
            n_districts = 0
            n_regionals = 0
            n_dcmps = 0
            cost = 0

            ekeys = []
            async for event in tpa.get_team_events_by_year(
                team_key=team.key, year=year
            ):
                if event.event_type == EventType.REGIONAL:
                    cost += 5000 if n_regionals == 0 else 4000
                    n_regionals += 1
                if event.event_type == EventType.DISTRICT:
                    cost += 2500 if n_districts < 2 else 1000
                    n_districts += 1
                if (
                    event.event_type
                    in [EventType.DISTRICT_CMP, EventType.DISTRICT_CMP_DIVISION]
                    and n_dcmps < 1
                ):
                    cost += 5000
                    n_dcmps += 1
                if event.event_type == EventType.CMP_DIVISION:
                    cost += 5000
                if event.event_type == EventType.OFFSEASON:
                    cost += 300

                ekeys.append(event.key)

            if cost == 2500:
                cost = 5000

            if len(ekeys) == 0:
                continue

            matches = [
                m
                async for m in tpa.get_team_matches_by_year(
                    team_key=team.key, year=year
                )
            ]

            if len(matches) == 0:
                continue

            matches = list(filter(lambda m: m.event_key in ekeys, matches))

            v = cost / len(matches)

            costs_by_states[team.state_prov].append(v)
            wtf.append((team.key, v))
            data.append(v)

    print(pd.DataFrame(data).describe())

    for team, cost in sorted(wtf, key=lambda t: -t[1])[:10]:
        print(f"{team.rjust(7)}  ${cost}")

    for team, cost in sorted(wtf, key=lambda t: t[1])[:10]:
        print(f"{team.rjust(7)}  ${cost}")

    state_avgs = {k: statistics.mean(v) for k, v in costs_by_states.items()}
    for state, avg in sorted(state_avgs.items(), key=lambda t: -t[1]):
        print(state, avg)


@expose
async def costs2(year):
    async with tpa_cm() as tpa:
        team_costs = defaultdict(lambda: 0)
        team_matches = defaultdict(lambda: 0)
        n_regionals = defaultdict(lambda: 0)
        n_districts = defaultdict(lambda: 0)
        n_dcmps = defaultdict(lambda: 0)
        key_to_team = {}

        async for event in tqdm(tpa.get_events_by_year(year=year)):
            async for team in tpa.get_event_teams(event_key=event.key):
                cost = 0
                key_to_team[team.key] = team

                if event.event_type == EventType.REGIONAL:
                    cost += 5000 if n_regionals[team.key] == 0 else 4000
                    n_regionals[team.key] += 1
                if event.event_type == EventType.DISTRICT:
                    cost += 2500 if n_districts[team.key] < 2 else 1000
                    n_districts[team.key] += 1
                if (
                    event.event_type
                    in [EventType.DISTRICT_CMP, EventType.DISTRICT_CMP_DIVISION]
                    and n_dcmps[team.key] < 1
                ):
                    cost += 5000
                    n_dcmps[team.key] += 1
                if event.event_type == EventType.CMP_DIVISION:
                    cost += 5000
                if event.event_type == EventType.OFFSEASON:
                    cost += 300

                team_costs[team.key] += cost

            if event.event_type in [
                EventType.REGIONAL,
                EventType.DISTRICT,
                EventType.DISTRICT_CMP,
                EventType.DISTRICT_CMP_DIVISION,
                EventType.CMP_DIVISION,
                EventType.CMP_FINALS,
                EventType.FOC,
                EventType.OFFSEASON,
            ]:
                async for match in tpa.get_event_matches(event_key=event.key):
                    for alliance in [match.alliances.red, match.alliances.blue]:
                        for tk in alliance.team_keys:
                            team_matches[tk] += 1

    for k in team_costs.copy().keys():
        if team_matches[k] == 0:
            del team_costs[k]
        if team_costs[k] < 5000:
            del team_costs[k]

    cpm = {k: team_costs[k] / max(team_matches[k], 1) for k in team_costs.keys()}

    by_state = defaultdict(list)
    for k, cpm_ in cpm.items():
        team = key_to_team[k]
        if team.country == "USA":
            by_state[team.state_prov].append(cpm_)

    for k in by_state.keys():
        by_state[k] = statistics.mean(by_state[k])

    print(sorted(cpm.items(), key=lambda t: -t[1])[:10])
    print(sorted(cpm.items(), key=lambda t: t[1])[:10])
    print("----")
    print(sorted(by_state.items(), key=lambda t: -t[1])[:10])
    print(sorted(by_state.items(), key=lambda t: t[1])[:10])

    print(pd.DataFrame(cpm.values()).describe())

    with file_cm(get_savepath("cpm.csv"), "w+") as f:
        for k, cpm_ in cpm.items():
            print(f"{k},{key_to_team[k].state_prov},{cpm_}", file=f)


@expose
async def unused():
    def prime(n):
        return not any(n % i == 0 for i in range(2, n))

    n = 0
    async with tpa_cm() as tpa:
        for page in trange(MAX_TEAMS_PAGE_RANGE):
            async for team in tpa.get_teams(page_num=page):
                while n < team.team_number:
                    # print(n)

                    if (
                        (len(set(str(n))) in [1, 2])
                        and not any([c in str(n) for c in "0689"])
                        and n >= 325
                        and prime(n)
                    ):
                        print(n)

                    n += 1

                n += 1


@expose
async def non_1_seed_wins():
    wins = defaultdict(lambda: 0)
    years = list(range(2006, 2020))
    lens = {}

    async with tpa_cm() as tpa:
        for year in years:
            for bar, event in tqdm_bar(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    if e.event_type in EventType.STANDARD_EVENT_TYPES
                ]
            ):
                bar.set_description(event.key)
                async for alliance in tpa.get_event_alliances(event_key=event.key):
                    if alliance.status.status == "won" and "1" not in alliance.name:
                        for tk in alliance.picks:
                            wins[tk] += 1
                            if tk not in lens:
                                lens[tk] = (
                                    max(years)
                                    - (await tpa.get_team(team_key=tk)).rookie_year
                                    + 1
                                )

    print(sorted(wins.items(), key=lambda t: -t[1])[:50])


@expose
async def best_per_seed():
    records = defaultdict(lambda: defaultdict(lambda: {"wins": 0, "losses": 0}))

    async with tpa_cm() as tpa:
        for year in range(2006, 2021):
            for bar, event in tqdm_bar(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    if e.event_type in EventType.STANDARD_EVENT_TYPES
                ]
            ):
                bar.set_description(event.key)

                async for alliance in tpa.get_event_alliances(event_key=event.key):
                    for team in alliance.picks:
                        records[alliance.name][team][
                            "wins"
                        ] += alliance.status.record.wins
                        records[alliance.name][team][
                            "losses"
                        ] += alliance.status.record.losses

    for alliance_name, history in sorted(records.items(), key=lambda t: t[0]):
        table_data = []
        top = wilson_sort(
            {k: v for k, v in history.items() if (v["wins"] + v["losses"]) > 9}.items(),
            positive=lambda t: t[1]["wins"],
            negative=lambda t: t[1]["losses"],
        )
        for team, rec in top[:10]:
            table_data.append(
                [
                    team,
                    rec["wins"],
                    rec["losses"],
                    round(rec["wins"] / (max(rec["losses"] + rec["wins"], 1)) * 100, 1),
                ]
            )

        print(alliance_name)
        print(make_table(["Team", "Wins", "Loss", "WR%"], table_data))


@expose
async def epr():
    min_elim_appearances = 5
    psr_num = defaultdict(lambda: {"qf": 0, "sf": 0, "f": 0, "w": 0, "": 0})
    ppsr_num = defaultdict(lambda: {i: 0 for i in range(9)})
    team_colors = dict()
    event_counts = defaultdict(lambda: 0)
    elim_counts = defaultdict(lambda: 0)
    unpicked_points = 0
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            2010,
            2020,
            lambda e: (
                e.event_type in EventType.SEASON_EVENT_TYPES
                and e.key not in ["2015micmp", "2016micmp"]
                and "(Cancelled)" not in e.name
            ),
        ):
            finishes = defaultdict(lambda: "")
            seeds = defaultdict(lambda: 0)
            good = True
            async for alliance in tpa.get_event_alliances(event_key=event.key):
                try:
                    int(alliance.name[-1])
                except:
                    good = False
                    break

                for tk in alliance.picks:
                    finishes[tk] = alliance.status.level
                    seeds[tk] = int(alliance.name[-1])
                    elim_counts[tk] += 1
            if not good:
                continue

            async for team in tpa.get_event_teams(event_key=event.key):
                psr_num[team.key][finishes[team.key]] += 1
                ppsr_num[team.key][seeds[team.key]] += 1
                event_counts[team.key] += 1
                team_colors[team.key] = team.region.color

        psr = {}
        for team, finishes in psr_num.items():
            psr[team] = (
                finishes["qf"] * 1
                + finishes["sf"] * 2
                + finishes["f"] * 3
                + finishes["w"] * 4
                + finishes[""] * unpicked_points
            ) / event_counts[team]

        ppsr = {}
        for team, seeds in ppsr_num.items():
            fake_psr_num = defaultdict(
                lambda: {"qf": 0, "sf": 0, "f": 0, "w": 0, "": 0}
            )
            n = 0
            for seed, count in seeds.items():
                n += count
                d = {
                    0: "",
                    1: "w",
                    2: "f",
                    3: "sf",
                    4: "sf",
                    5: "qf",
                    6: "qf",
                    7: "qf",
                    8: "qf",
                }
                fake_psr_num[team][d[seed]] += count

            ppsr[team] = (
                fake_psr_num[team]["qf"] * 1
                + fake_psr_num[team]["sf"] * 2
                + fake_psr_num[team]["f"] * 3
                + fake_psr_num[team]["w"] * 4
                + fake_psr_num[team][""] * unpicked_points
            ) / event_counts[team]

        epsr = {k: psr[k] - ppsr[k] for k in psr.keys()}
        xpsr = {k: psr[k] * epsr[k] for k in psr.keys()}
        f = open("out.txt", "w+")
        print(
            make_table(
                ["Team", "Events", "PSR", "PPSR", "EPSR", "xPSR"],
                [
                    [
                        t[3:],
                        event_counts[t],
                        round(psr[t], 3),
                        round(ppsr[t], 3),
                        round(epsr[t], 3),
                        round(xpsr[t], 3),
                    ]
                    for t in sorted(psr.keys(), key=lambda k: -xpsr[k])
                    if elim_counts[t] >= min_elim_appearances
                ],
            ),
            file=f,
        )

        fig = go.Figure()
        keys = [k for k in epsr.keys() if elim_counts[k] >= min_elim_appearances]
        fig.add_trace(
            go.Scatter(
                x=[psr[k] for k in keys],
                y=[epsr[k] for k in keys],
                text=[f"{k[3:]} ({event_counts[k]})" for k in keys],
                marker_color=[team_colors[k] for k in keys],
                mode="markers",
            )
        )
        fig.update_layout(
            title="FRC Expected Playoff Success Rating vs Playoff Success Rating",
            xaxis_title="Playoff Success Rating",
            yaxis_title="Expected Playoff Success Rating",
        )
        fig.add_annotation(
            x=3.5,
            y=0.75,
            showarrow=False,
            text="Historically good,\noverperforms",
        )
        fig.add_annotation(
            x=3.5,
            y=-1,
            showarrow=False,
            text="Historically good,\nunderperforms",
        )
        fig.add_annotation(
            x=0,
            y=-1,
            showarrow=False,
            text="Historically bad,\nunderperforms",
        )
        fig.add_annotation(
            x=0,
            y=0.75,
            showarrow=False,
            text="Historically bad,\noverperforms",
        )

        fig.show()


@expose
async def generate_regions():
    async with tpa_cm() as tpa:
        f = open("py/data/regions.json", "w+")
        region = {}
        async for district in tpa.get_districts_by_year(year=CURRENT_YEAR):
            async for district_team in tpa.get_district_teams(
                district_key=district.key
            ):
                region[district_team.key] = district.abbreviation

        async for team in tpa.get_all_teams_by_year(year=CURRENT_YEAR):
            if team.key not in region:
                region[team.key] = team.state_prov

        json.dump(region, f)


@expose
async def pyth_opr(event: str, n: Optional[float] = None):
    async with tpa_cm() as tpa:
        count = defaultdict(lambda: 0)
        good = defaultdict(lambda: 0)
        partner_oprs = defaultdict(list)
        opp_oprs = defaultdict(list)
        oprs = await tpa.get_event_op_rs(event_key=event)
        event_details = await tpa.get_event(event_key=event)
        async for match in tpa.get_event_matches(event_key=event):
            if match.comp_level != "qm":
                continue

            for winner in match.alliances.winner.team_keys:
                good[winner] += 1

            red_total_opr = sum([oprs.oprs[k] for k in match.alliances.red.team_keys])
            blue_total_opr = sum([oprs.oprs[k] for k in match.alliances.blue.team_keys])
            for a in [match.alliances.red, match.alliances.blue]:
                for tk in a.team_keys:
                    count[tk] += 1
                    partner_oprs[tk].append(
                        red_total_opr if a.color == Color.RED else blue_total_opr
                    )
                    opp_oprs[tk].append(
                        red_total_opr if a.color == Color.BLUE else blue_total_opr
                    )

        keys = sorted(list(good.keys()), key=lambda k: int(k[3:]))

        if n is None:
            ns = {
                tk: ((sum(partner_oprs[tk]) + sum(opp_oprs[tk])) / count[tk]) ** 0.287
                for tk in keys
            }
        else:
            ns = {tk: n for tk in keys}

        luck = {
            tk: good[tk]
            - (1 / (1 + ((sum(opp_oprs[tk]) / sum(partner_oprs[tk])) ** ns[tk])))
            * count[tk]
            for tk in keys
        }
        fig = go.Figure(
            data=go.Scatter(
                y=[luck[k] for k in keys],
                x=[oprs.oprs[k] for k in keys],
                text=[k[3:] for k in keys],
                textposition="bottom center",
                mode="markers+text",
            )
        )
        fig.update_layout(
            title=f"{event_details.year} {event_details.name} - n := {n}",
            xaxis_title="OPR",
            yaxis_title="Wins Above Expected",
        )
        fig.show()


@expose
async def sponsors():
    sponsored_by = defaultdict(list)

    async with tpa_cm() as tpa:
        async for team in tpa.get_all_teams_by_year(year=2022):
            if team.state_prov in [
                "Massachusetts",
                "Maine",
                "Vermont",
                "New Hampshire",
                "Connecticut",
                "Rhode Island",
            ]:
                # if True:
                print(team.team_number)

                delim_matches = re.findall(r"[^_]/\w|\w\&\w", team.name)
                sponsors = []
                end_of_last_sponsor = 0
                for i in range(len(team.name) - 3):
                    if team.name[i : i + 3] in delim_matches:
                        sponsors.append(team.name[end_of_last_sponsor : i + 1])
                        end_of_last_sponsor = i + 2
                sponsors.append(team.name[end_of_last_sponsor:])

                for sponsor in sponsors:
                    key = sponsor.strip().replace(",", ";")
                    if team.team_number not in sponsored_by[sponsor]:
                        sponsored_by[key].append(team.team_number)

    with open("sponsors.csv", "w+") as f:
        for sponsor, teams in sorted(sponsored_by.items(), key=lambda t: -len(t[1])):
            f.write(f'{sponsor},{len(teams)},{",".join([str(n) for n in teams])}\n')


@expose
async def goat():
    async with tpa_cm() as tpa:
        sums = defaultdict(lambda: 0)
        counts = defaultdict(lambda: 0)
        async for team in tpa.get_all_teams():
            for year, elo in sorted(team.yearly_elos.items(), key=lambda t: t[0]):
                if year in [2020, 2021]:
                    continue

                sums[team.team_number] += elo - 25
                counts[team.team_number] += 1

        print(
            make_table(
                col_names=["Team", "Sum", "Avg", "Count"],
                row_vals=[
                    [k, round(sums[k], 2), round(sums[k] / counts[k], 2), counts[k]]
                    for k in sorted(
                        list(sums.keys()),
                        key=lambda k_: -sums[k_],
                    )
                ],
            )
        )

        print("==============================================")
        print(
            make_table(
                col_names=["Team", "Sum", "Avg", "Count"],
                row_vals=[
                    [k, round(sums[k], 2), round(sums[k] / counts[k], 2), counts[k]]
                    for k in sorted(
                        list(sums.keys()),
                        key=lambda k_: -sums[k_] / counts[k_],
                    )
                ],
            )
        )


@expose
async def consecutive_div_finals():
    made = defaultdict(list)
    start = 2004
    async with tpa_cm() as tpa:
        for year in range(start, CURRENT_YEAR_RANGE):
            async for event in all_events_with_bar(
                tpa,
                year_start=year,
                year_end=year,
                condition=lambda e: e.event_type == EventType.CMP_DIVISION,
            ):
                async for award in tpa.get_event_awards(event_key=event.key):
                    if award.award_type in [AwardType.FINALIST, AwardType.WINNER]:
                        for recipient in award.recipient_list:
                            made[recipient.team_key].append(year)

    def active_streak(years):
        n = 0
        if 2023 in years:
            yr = 2023

            while yr in years:
                n += 1
                yr -= 1

                while yr in [2020, 2021]:
                    yr -= 1

        return n

    def longest_streak(years):
        best = 0
        curr = 0
        for y in range(start, CURRENT_YEAR_RANGE):
            if y in [2020, 2021]:
                continue

            if y in years:
                curr += 1
            else:
                best = max(best, curr)
                curr = 0

        return max(best, curr)

    f = longest_streak
    for tk, years in sorted(made.items(), key=lambda t: -f(t[1])):
        active = f(years)
        if active > 2:
            print(
                f'{tk[3:].rjust(4)} - {", ".join([str(s) for s in years[-active:]])} ({active})'
            )


@expose
async def youngest_einstein():
    ages = defaultdict(list)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2004,
            year_end=2023,
            condition=lambda e: e.event_type == EventType.CMP_DIVISION,
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                if award.award_type == AwardType.WINNER:
                    for recipient in award.recipient_list:
                        team = await tpa.get_team(team_key=recipient.team_key)
                        ages[event.year - team.rookie_year].append(
                            [team.team_number, event.year]
                        )

    for i in range(0, 3):
        pprint(sorted(ages[i], key=lambda t: (t[1], t[0])))


@expose
async def worst_einstein_record():
    records = defaultdict(lambda: WltRecord())

    async with tpa_cm() as tpa:
        for year in range(2000, CURRENT_YEAR_RANGE):
            for bar, event in tqdm_bar(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    if e.event_type == EventType.CMP_FINALS
                ]
            ):
                bar.set_description(event.key)
                async for match in tpa.get_event_matches(event_key=event.key):
                    if (
                        match.alliances.blue.score == -1
                        and match.alliances.red.score == -1
                    ):
                        continue

                    if match.winning_alliance in ["red", "blue"]:
                        for tk in getattr(
                            match.alliances, match.winning_alliance
                        ).team_keys:
                            records[tk].wins += 1
                        for tk in getattr(
                            match.alliances, OPPOSITE_COLOR[match.winning_alliance]
                        ).team_keys:
                            records[tk].losses += 1
                    else:
                        for c in ["red", "blue"]:
                            for tk in getattr(match.alliances, c).team_keys:
                                records[tk].ties += 1

    table = []
    for combo, record in wilson_sort(
        records.items(),
        positive=lambda t: t[1].wins,
        negative=lambda t: t[1].ties + t[1].losses,
        z=1.0,
        minimum_total=4,
    )[:75]:
        table.append(
            [combo[3:]]
            + [
                record.wins,
                record.losses,
                record.ties,
                round(
                    record.wins / (record.wins + record.losses + record.ties) * 100, 2
                ),
            ]
        )

    print(make_table(["T1", "W", "L", "T", "%"], table))


@expose
async def worst_champs_playoffs_records():
    records = defaultdict(lambda: WltRecord())

    async with tpa_cm() as tpa:
        for year in range(2000, CURRENT_YEAR_RANGE):
            for bar, event in tqdm_bar(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    # if e.event_type in [EventType.CMP_FINALS, EventType.CMP_DIVISION]
                    # if e.event_type in EventType.SEASON_EVENT_TYPES
                    if e.event_type in EventType.NON_CMP_EVENT_TYPES
                ]
            ):
                bar.set_description(event.key)
                async for match in tpa.get_event_matches(event_key=event.key):
                    if (
                        match.alliances.blue.score == -1
                        and match.alliances.red.score == -1
                    ) or match.comp_level == "qm":
                        continue

                    if match.winning_alliance in ["red", "blue"]:
                        for tk in getattr(
                            match.alliances, match.winning_alliance
                        ).team_keys:
                            records[tk].wins += 1
                        for tk in getattr(
                            match.alliances, OPPOSITE_COLOR[match.winning_alliance]
                        ).team_keys:
                            records[tk].losses += 1
                    else:
                        for c in ["red", "blue"]:
                            for tk in getattr(match.alliances, c).team_keys:
                                records[tk].ties += 1

    table = []
    for combo, record in wilson_sort(
        records.items(),
        positive=lambda t: t[1].wins,
        negative=lambda t: t[1].ties + t[1].losses,
        z=1.0,
        minimum_total=20,
    )[:100]:
        table.append(
            [combo[3:]]
            + [
                record.wins,
                record.losses,
                record.ties,
                round(
                    record.wins / (record.wins + record.losses + record.ties) * 100, 2
                ),
            ]
        )

    with open("out.txt", "w+") as f:
        print(make_table(["T1", "W", "L", "T", "%"], table), file=f)

    print(make_table(["T1", "W", "L", "T", "%"], table))


@expose
async def most_finals_below_seed(seed: int):
    awards_to_count = [AwardType.FINALIST, AwardType.WINNER]
    count = defaultdict(lambda: 0)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2004,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            awards = [a async for a in tpa.get_event_awards(event_key=event.key)]
            async for alliance in tpa.get_event_alliances(event_key=event.key):
                try:
                    a_seed = int(alliance.name[-1])
                    if a_seed >= seed:
                        for team_key in alliance.picks:
                            team_awards = list(
                                filter(
                                    lambda a: team_key
                                    in [r.team_key for r in a.recipient_list]
                                    and a.award_type in awards_to_count,
                                    awards,
                                )
                            )

                            if len(team_awards) > 0:
                                count[team_key] += 1
                except:
                    break

    pprint(sorted(count.items(), key=lambda t: -t[1])[:100])


@expose
async def highest_einstein_alliance():
    awards_to_count = [AwardType.WINNER]
    seeds = defaultdict(list)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2004,
            year_end=CURRENT_YEAR,
            condition=lambda e: e.event_type == EventType.CMP_DIVISION,
        ):
            awards = [a async for a in tpa.get_event_awards(event_key=event.key)]
            async for alliance in tpa.get_event_alliances(event_key=event.key):
                try:
                    a_seed = int(alliance.name[-1])
                    for team_key in alliance.picks:
                        team_awards = list(
                            filter(
                                lambda a: team_key
                                in [r.team_key for r in a.recipient_list]
                                and a.award_type in awards_to_count,
                                awards,
                            )
                        )

                        if len(team_awards) > 0:
                            seeds[team_key].append(a_seed)
                except:
                    break

    for k, v in sorted(seeds.items(), key=lambda t: -statistics.mean(t[1])):
        if len(v) < 2:
            continue

        print(f"{k} - {v} - {round(statistics.mean(v), 2)}")


@expose
async def most_div_finals_without_win():
    finalist_count = defaultdict(lambda: 0)
    win_count = defaultdict(lambda: 0)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2004,
            year_end=CURRENT_YEAR,
            # condition=lambda e: e.event_type == EventType.CMP_DIVISION,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                if award.award_type == AwardType.FINALIST:
                    for recipient in award.recipient_list:
                        finalist_count[recipient.team_key] += 1

                if award.award_type == AwardType.WINNER:
                    for recipient in award.recipient_list:
                        win_count[recipient.team_key] += 1

    for k, v in sorted(finalist_count.items(), key=lambda t: -t[1]):
        if win_count[k] > 0:
            continue
        if v < 4:
            continue

        print(f"{k[3:]} - {v}")


@expose
async def ca_3():
    async with tpa_cm() as tpa:
        async for team in tpa.get_all_teams_by_year(year=2023):
            if team.state_prov in ["CA", "California"]:
                events = [
                    e
                    async for e in tpa.get_team_events_by_year(
                        team_key=team.key, year=2023
                    )
                    if e.event_type == EventType.REGIONAL
                ]
                if len(events) >= 3:
                    print(f"{team.team_number}, {len(events)}")


@expose
async def nonca_in_ca():
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2023,
            year_end=2023,
            condition=lambda e: e.state_prov in ["CA", "California"]
            and e.event_type == EventType.REGIONAL,
        ):
            async for team in tpa.get_event_teams(event_key=event.key):
                if team.state_prov not in ["CA", "California"]:
                    events = [
                        e
                        async for e in tpa.get_team_events_by_year(
                            team_key=team.key, year=2023
                        )
                        if e.event_type == EventType.REGIONAL
                    ]
                    if len(events) >= 3:
                        print(f"{team.team_number}, {len(events)}")


@expose
async def touched_einstein_carpet():
    counts = defaultdict(int)
    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=2014,
            year_end=2023,
            condition=lambda e: e.event_type == EventType.CMP_FINALS,
        ):
            shown_in_year = set()
            async for match in tpa.get_event_matches(event_key=event.key):
                for team in match.alliances.blue.team_keys:
                    shown_in_year.add(team)
                for team in match.alliances.red.team_keys:
                    shown_in_year.add(team)

            for t in shown_in_year:
                counts[t] += 1

    pprint(sorted(counts.items(), key=lambda t: -t[1]))

    print(len(counts.keys()))


@expose
async def worlds_award_winners():
    award_winners = defaultdict(set)

    async with tpa_cm() as tpa:
        async for event in all_events_with_bar(
            tpa,
            year_start=1992,
            year_end=2023,
            condition=lambda e: e.event_type == EventType.CMP_FINALS,
        ):
            async for award in tpa.get_event_awards(event_key=event.key):
                for recipient in award.recipient_list:
                    if recipient.team_key not in [None, ""]:
                        award_winners[award.award_type].add(int(recipient.team_key[3:]))
                    elif (
                        maybe_team := {
                            ("2007cmp", AwardType.WOODIE_FLOWERS): 111,
                            ("2008cmp", AwardType.WOODIE_FLOWERS): 188,
                        }.get((event.key, award.award_type), None)
                    ) is not None:
                        award_winners[award.award_type].add(maybe_team)
                    elif award.award_type in [
                        AwardType.CHAIRMANS,
                        AwardType.WINNER,
                        AwardType.WOODIE_FLOWERS,
                        AwardType.DEANS_LIST,
                    ]:
                        print(
                            f"No team for {event.year} {award.name} winner - {recipient.awardee}"
                        )

    for award_type, winners in award_winners.items():
        if award_type in [
            AwardType.CHAIRMANS,
            AwardType.WINNER,
            AwardType.WOODIE_FLOWERS,
            AwardType.DEANS_LIST,
        ]:
            l = list(winners)
            print(award_type)
            for t in sorted(l):
                print(t)

            print("")

    print(
        award_winners[AwardType.CHAIRMANS]
        & award_winners[AwardType.WINNER]
        & award_winners[AwardType.WOODIE_FLOWERS]
    )


@expose
async def important_event_winners():
    winners = defaultdict(list)

    winners[0].extend(
        [
            1,
            65,
            240,
            201,
            469,
            68,
            308,
            27,
            469,
            71,
            980,
            269,
            33,
            233,
            868,
            71,
            1625,
            910,
            111,
            1114,
            494,
            2056,
        ]
    )

    async with tpa_cm() as tpa:
        for n, event_group in enumerate(
            [
                ["iri"],
                ["cc"],
                ["cmp", "cmptx", "cmpmo", "cmpmi"],
            ]
        ):
            async for event in all_events_with_bar(
                tpa,
                year_start=1992,
                year_end=2023,
                condition=lambda e: e.event_code in event_group,
            ):
                awards = [a async for a in tpa.get_event_awards(event_key=event.key)]
                if len(awards) > 0:
                    for award in awards:
                        if award.award_type == AwardType.WINNER:
                            for recipient in award.recipient_list:
                                winners[n].append(int(recipient.team_key[3:]))

                else:
                    matches = [
                        m async for m in tpa.get_event_matches(event_key=event.key)
                    ]

                    matches = list(filter(lambda m: m.comp_level == "f", matches))
                    matches.sort(key=lambda m: m.match_number)

                    for x in matches[0].alliances.winner.team_keys:
                        winners[n].append(int(x[3:]))

    for n in [0, 1, 2]:
        for t in sorted(list(set(winners[n]))):
            print(t)

        print("-------------")

    for n in [0, 1, 2]:
        result = {
            freq: sorted(
                [num for num, count in Counter(winners[n]).items() if count == freq]
            )
            for freq in set(Counter(winners[n]).values())
        }

        pprint(result)

    pprint(sorted(list(set(winners[0]) & set(winners[1]))))
    pprint(sorted(list(set(winners[0]) & set(winners[2]))))
    pprint(sorted(list(set(winners[1]) & set(winners[2]))))


@expose
async def event_count_by_region(year: int):
    plays = defaultdict(int)
    team_to_district_map = {}

    async with tpa_cm() as tpa:
        async for district in tpa.get_districts_by_year(year=year):
            async for team in tpa.get_district_teams(district_key=district.key):
                team_to_district_map[team.key] = district.display_name

        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=year,
            year_end=year,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES
            and e.event_type not in EventType.CMP_EVENT_TYPES,
        ):
            async for team in tpa.get_event_teams(event_key=event.key):
                if team.country not in ["USA", "Canada"]:
                    continue

                region = team_to_district_map.get(team.key, team.state_prov)
                plays[(team.key, region)] += 1

    max_plays = 0
    region_plays = defaultdict(lambda: defaultdict(int))
    for (_, region), count in plays.items():
        region_plays[region][count] += 1
        max_plays = max(max_plays, count)

    maybe_dash = lambda n: "" if n == 0 else n

    print(
        make_table(
            col_names=["Region"]
            + [str(x) for x in range(1, max_plays + 1)]
            + [str(x) + " (%)" for x in range(1, max_plays + 1)],
            row_vals=[
                [r]
                + [maybe_dash(count_vals[c]) for c in range(1, max_plays + 1)]
                + [
                    (
                        round(100 * count_vals[c] / sum(list(count_vals.values())), 1)
                        if count_vals[c] > 0
                        else ""
                    )
                    for c in range(1, max_plays + 1)
                ]
                for r, count_vals in sorted(
                    region_plays.items(), key=lambda rc: -sum(list(rc[1].values()))
                )
            ],
        )
    )


@expose
async def award_count_by_region(year: int):
    region_awards = defaultdict(lambda: defaultdict(int))
    team_to_district_map = {}
    played = set()

    async with tpa_cm() as tpa:
        async for district in tpa.get_districts_by_year(year=year):
            async for team in tpa.get_district_teams(district_key=district.key):
                team_to_district_map[team.key] = district.display_name

        cmp_event_keys = [
            e.key
            async for e in tpa.get_events_by_year(year=year)
            if e.event_type in EventType.CMP_EVENT_TYPES
        ]

        async for event in all_events_with_bar(
            tpa,
            year_start=year,
            year_end=year,
            condition=lambda e: e.event_type in EventType.SEASON_EVENT_TYPES,
        ):
            async for team in tpa.get_event_teams(event_key=event.key):
                played.add(team.key)

        async for team in all_teams_with_bar(
            tpa, year=year, condition=lambda t: t.key in played
        ):
            if team.country not in ["USA", "Canada"]:
                continue

            awards = [
                a
                async for a in tpa.get_team_awards_by_year(team_key=team.key, year=year)
                if (
                    a.award_type
                    not in [AwardType.WINNER, AwardType.FINALIST, AwardType.WILDCARD]
                )
                and (a.event_key not in cmp_event_keys)
            ]

            region_awards[team_to_district_map.get(team.key, team.state_prov)][
                len(awards)
            ] += 1

    max_plays = 0
    for _, award_counts in region_awards.items():
        for count, _ in award_counts.items():
            max_plays = max(max_plays, count)

    maybe_dash = lambda n: "" if n == 0 else n

    print(
        make_table(
            col_names=["Region"]
            + [str(x) for x in range(0, max_plays + 1)]
            + [str(x) + " (%)" for x in range(0, max_plays + 1)],
            row_vals=[
                [r]
                + [maybe_dash(count_vals[c]) for c in range(0, max_plays + 1)]
                + [
                    (
                        round(100 * count_vals[c] / sum(list(count_vals.values())), 1)
                        if count_vals[c] > 0
                        else ""
                    )
                    for c in range(0, max_plays + 1)
                ]
                for r, count_vals in sorted(
                    region_awards.items(), key=lambda rc: -sum(list(rc[1].values()))
                )
            ],
        )
    )


@expose
async def years_since_last_cmp(year: int):
    async with tpa_cm() as tpa:
        regional_team_keys = set()
        district_team_keys = set()
        async for district in tpa.get_districts_by_year(year=year):
            async for team in tpa.get_district_teams(district_key=district.key):
                district_team_keys.add(team.key)

        async for event in all_events_with_bar(
            tpa=tpa,
            year_start=year,
            year_end=year,
            condition=lambda e: e.event_type not in EventType.CMP_EVENT_TYPES
            and e.event_type == EventType.REGIONAL,
        ):
            async for team in tpa.get_event_teams(event_key=event.key):
                if team.key not in district_team_keys:
                    regional_team_keys.add(team.key)

        years_since = {}
        for team in tqdm_sync(list(regional_team_keys)):
            events = [
                event
                async for event in tpa.get_team_events(team_key=team)
                if (
                    event.event_type in EventType.CMP_EVENT_TYPES
                    and event.year not in [2020, 2021, year]
                    and event.year < year
                )
            ]
            events.sort(key=lambda e: e.year)

            if len(events) == 0:
                years_since[int(team[3:])] = "-"
            else:
                years_since[int(team[3:])] = year - events[-1].year - 2

    def sorter(t):
        n, s = t
        if isinstance(s, str):
            return (99, n)

        return (s, n)

    with open("last_cmp.txt", "w+") as f:
        for k, v in sorted(years_since.items(), key=sorter):
            print(f"{k},{v}", file=f)


@expose
async def first_dcmp():
    with open("in.txt", "r") as f:
        teams = [int(l.strip()) for l in f.readlines()]

    has_attended = set()

    async with tpa_cm() as tpa:
        # for t in tqdm_sync(teams):
        #     async for event in tpa.get_team_events(team_key=f"frc{t}"):
        #         if (
        #             event.event_type
        #             in [
        #                 EventType.DISTRICT_CMP,
        #                 EventType.DISTRICT_CMP_DIVISION,
        #             ]
        #             and event.year < CURRENT_YEAR
        #         ):
        #             has_attended.add(t)
        #             break

        async for event in all_events_with_bar(
            tpa,
            year_start=1992,
            year_end=CURRENT_YEAR - 1,
            condition=lambda e: e.event_type in [
                    EventType.DISTRICT_CMP,
                    EventType.DISTRICT_CMP_DIVISION,
                ]
        ):
            async for team in tpa.get_event_teams(event_key=event.key):
                has_attended.add(team.team_number)

    for t in teams:
        if t not in has_attended:
            print(t)
