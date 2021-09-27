from collections import defaultdict
from protos.tpa import Event
from typing import Dict, List
from py.util import sort_events
from tabulate import tabulate

import numpy as np
import bar_chart_race as bcr

from datetime import datetime

import pandas as pd

import plotly.graph_objects as go
from rich import print
from tqdm.rich import trange, tqdm

from py.cli import expose
from py.tba import AwardType, EventType
from py.tpa import tpa_cm


@expose
async def most_states():
    states = defaultdict(set)
    async with tpa_cm() as tpa:
        async for year in trange(1992, 2022):
            async for event in tpa.get_events_by_year(year=year):
                async for award in tpa.get_event_awards(event_key=event.key):
                    for recipient in award.recipient_list:
                        if len(event.state_prov) > 0:
                            states[recipient.team_key].add(event.state_prov)

    counts = {t: len(s) for t, s in states.items()}
    print(sorted(counts.items(), key=lambda t: -(t[1]))[:25])


@expose
async def wffa_families():
    winners = defaultdict(list)

    async with tpa_cm() as tpa:
        for year in trange(1992, 2022):
            async for event in tpa.get_events_by_year(year=year):
                if event.event_type in EventType.CMP_EVENT_TYPES:
                    continue

                async for award in tpa.get_event_awards(event_key=event.key):
                    if award.award_type == 3:
                        for recipient in award.recipient_list:
                            last_name = recipient.awardee.split(" ")[-1]
                            winners[(last_name)].append(
                                (event.key, recipient.awardee, recipient.team_key)
                            )

    for (last_name), event_awardee_list in winners.items():
        if len(event_awardee_list) > 1:
            print(f"* {last_name} family?: ", end="")
            s = [f"{a} ({t}) ({e})" for e, a, t in event_awardee_list]
            print(", ".join(s))


@expose
async def wffa_info():
    async with tpa_cm() as tpa:
        async for year in trange(1992, 2022):
            async for event in tpa.get_events_by_year(year=year):
                award_type = (
                    "WFA" if event.event_type in EventType.CMP_EVENT_TYPES else "WFFA"
                )
                async for award in tpa.get_event_awards(event_key=event.key):
                    if award.award_type == AwardType.WOODIE_FLOWERS:
                        for recipient in award.recipient_list:
                            tcity, tstate, tcountry = "", "", ""
                            if len(recipient.team_key) > 0:
                                team = await tpa.get_team(team_key=recipient.team_key)
                                tcity, tstate, tcountry = (
                                    team.city,
                                    team.state_prov,
                                    team.country,
                                )

                            print(
                                f"{award_type}\t{event.key}\t{recipient.awardee}\t{recipient.team_key}\t"
                                + f"{tcity}\t{tstate}\t{tcountry}\t"
                                + f"{event.city}\t{event.state_prov}\t{event.country}"
                            )


@expose
async def banner_records():
    count = defaultdict(lambda: 0)
    data = []
    async with tpa_cm() as tpa:
        for year in trange(1992, 2022):
            async for event in tpa.get_events_by_year(year=year):
                if event.event_type == EventType.OFFSEASON:
                    continue

                async for award in tpa.get_event_awards(event_key=event.key):
                    if award.award_type in AwardType.BLUE_BANNER_AWARDS:
                        for recipient in award.recipient_list:
                            if len(recipient.team_key) > 0:
                                count[recipient.team_key] += 1

            top = sorted(count.items(), key=lambda t: -t[1])[0]
            data.append((year, top))

    for year, (team_key, c) in data:
        print(f"{year},{team_key},{c}")


@expose
async def banner_compare(*teams):
    history = defaultdict(list)
    async with tpa_cm() as tpa:
        for year in trange(1992, 2022):
            for team in teams:
                count = 0
                async for award in tpa.get_team_awards_by_year(
                    team_key=f"frc{team}", year=year
                ):
                    if award.award_type in AwardType.BLUE_BANNER_AWARDS:
                        event = await tpa.get_event(event_key=award.event_key)
                        if event.event_type != EventType.OFFSEASON:
                            count += 1

                last = 0 if len(history[team]) == 0 else history[team][-1]
                history[team].append(last + count)

    fig = go.Figure()
    for team, banner_history in sorted(history.items(), key=lambda t: t[0]):
        fig.add_trace(
            go.Scatter(
                x=list(range(1992, 2022)),
                y=banner_history,
                mode="lines",
                name=team,
            )
        )

    fig.show()


@expose
async def banner_bar_chart():
    async with tpa_cm() as tpa:
        date_to_events = defaultdict(list)  # type: Dict[str, List[Event]]
        for year in trange(1992, 2022):
            for event in sort_events(
                [
                    e
                    async for e in tpa.get_events_by_year(year=year)
                    if e.event_type in EventType.SEASON_EVENT_TYPES
                ]
            ):
                date_to_events[event.end_date].append(event)

        all_teams = [str(n) for n in range(1, 10000)]
        df = pd.DataFrame(columns=all_teams, dtype="int32")
        banners = {k: 0 for k in all_teams}
        for date, events in tqdm(
            sorted(
                date_to_events.items(),
                key=lambda t: datetime.strptime(t[0], "%Y-%m-%d"),
            )
        ):
            for event in events:
                async for award in tpa.get_event_awards(event_key=event.key):
                    if award.award_type in AwardType.BLUE_BANNER_AWARDS:
                        for recipient in award.recipient_list:
                            if (recipient.team_key is not None) and (
                                len(recipient.team_key) > 3
                            ):
                                banners[recipient.team_key[3:]] += 1

            df = df.append(
                pd.DataFrame(
                    [[int(banners[t]) for t in all_teams]],
                    columns=all_teams,
                    dtype="int32",
                    index=[date],
                )
            )

    df = df.loc[:, (df != 0).any(axis=0)]
    bcr.bar_chart_race(
        df=df,
        filename=f"banner_history.mp4",
        n_bars=25,
        title="Top 25 in Blue Banners 1992-2021",
        period_length=500,
        steps_per_period=10 * 3,
    )
