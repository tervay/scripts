import statistics
from collections import defaultdict

import pandas as pd
from rich import print
from tqdm.asyncio import tqdm
from tqdm.rich import tqdm as tqdm_sync
from tqdm.rich import trange

from py.cli import expose
from py.tba import EventType, tba
from py.tpa import tpa_cm
from py.util import (
    MAX_TEAMS_PAGE_NUM,
    MAX_TEAMS_PAGE_RANGE,
    file_cm,
    filter_completed_events,
    filter_official_events,
    flatten_lists,
    flatten_lists_async,
    get_savepath,
    make_table,
    tqdm_bar,
    tqdm_bar_async,
    wilson_sort,
)


@expose
def about(num):
    print(tba.team(num, simple=True))


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
    n = 0
    async with tpa_cm() as tpa:
        for page in trange(MAX_TEAMS_PAGE_RANGE):
            async for team in tpa.get_teams(page_num=page):
                while n < team.team_number:
                    # print(n)

                    if (
                        (len(set(str(n))) in [1, 2])
                        and not any([c in str(n) for c in "04689"])
                        and n >= 1000
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
        for (team, rec) in top[:10]:
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
