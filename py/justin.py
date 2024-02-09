from rich import print
from tqdm import tqdm

from py.cli import expose
from py.tpa.context_manager import tpa_cm
from py.util import calculate_alliance_pts, calculate_qual_pts, make_table

team_events = [
    [2791, "2012nh"],
    [2791, "2012ct"],
    [2791, "2013nhma"],
    [2791, "2013mawo"],
    [2791, "2014nytr"],
    [2791, "2014nytv"],
    [2791, "2015nytr"],
    [2791, "2015nyro"],
    [2791, "2016nytr"],
    [2791, "2016nyro"],
    [2791, "2017nytr"],
    [2791, "2017nyny"],
    [2791, "2017cur"],
    [2791, "2017iri"],
    [340, "2018nyut"],
    [340, "2018nyro"],
    [340, "2018tes"],
    [340, "2018iri"],
    [5254, "2018nyrr"],
    [5254, "2018nytv"],
    [2791, "2019nytr"],
    [5254, "2019nyro"],
    [5254, "2019ohcl"],
    [2791, "2019dar"],
    [2791, "2019bc"],
    [5254, "2019nyrr"],
    [2713, "2021nhbb"],
    [2713, "2022week0"],
    [2713, "2022nhsea"],
    [2713, "2022necmp2"],
    [2713, "2022bc"],
    [2713, "2022mesh"],
    [2713, "2022nhmm"],
    [2713, "2022mabil"],
    [2713, "2022nhbb"],
    [2713, "2023mabri"],
    [2713, "2023mabos"],
    [2713, "2023necmp2"],
    [2713, "2023dal"],
    [2713, "2023bc"],
    [2713, "2023nhmm"],
]


@expose
async def events_match_stats():
    with open("out.csv", "w+") as f:
        async with tpa_cm() as tpa:
            for team_number, event_key in tqdm(team_events):
                event = await tpa.get_event(event_key=event_key)
                async for match in tpa.get_team_event_matches(
                    team_key=f"frc{team_number}", event_key=event_key
                ):
                    result = "T"

                    if (
                        match.alliances.red.score == -1
                        or match.alliances.blue.score == -1
                    ):
                        continue

                    if (
                        event.year == 2015
                        and match.alliances.red.score != match.alliances.blue.score
                    ):
                        result = (
                            "W"
                            if any(
                                [
                                    (
                                        match.alliances.red.score
                                        > match.alliances.blue.score
                                    )
                                    and (
                                        f"frc{team_number}"
                                        in match.alliances.red.team_keys
                                    ),
                                    (
                                        match.alliances.red.score
                                        < match.alliances.blue.score
                                    )
                                    and (
                                        f"frc{team_number}"
                                        in match.alliances.blue.team_keys
                                    ),
                                ]
                            )
                            else "L"
                        )
                    else:
                        if (
                            match.winning_alliance is not None
                            and len(match.winning_alliance) > 0
                        ):
                            result = (
                                "W"
                                if any(
                                    [
                                        match.winning_alliance == "red"
                                        and f"frc{team_number}"
                                        in match.alliances.red.team_keys,
                                        match.winning_alliance == "blue"
                                        and f"frc{team_number}"
                                        in match.alliances.blue.team_keys,
                                    ]
                                )
                                else "L"
                            )

                    f.write(
                        ",".join(
                            [
                                str(s)
                                for s in [
                                    team_number,
                                    event_key,
                                    event.event_type_string,
                                    event.playoff_type_string,
                                    event.week + 1,
                                    match.key,
                                    match.comp_level,
                                    match.alliances.red.team_keys[0][3:],
                                    match.alliances.red.team_keys[1][3:],
                                    match.alliances.red.team_keys[2][3:],
                                    match.alliances.blue.team_keys[0][3:],
                                    match.alliances.blue.team_keys[1][3:],
                                    match.alliances.blue.team_keys[2][3:],
                                    match.alliances.red.score,
                                    match.alliances.blue.score,
                                    result,
                                    match.time,
                                    match.actual_time,
                                ]
                            ]
                        )
                        + "\n"
                    )


@expose
async def events_district_pts():
    rows = []
    async with tpa_cm() as tpa:
        for team, event in tqdm(team_events):
            event = await tpa.get_event(event_key=event)
            alliances = [a async for a in tpa.get_event_alliances(event_key=event.key)]
            rankings = await tpa.get_event_rankings(event_key=event.key)
            a_pts = calculate_alliance_pts(
                alliances=alliances,
                team_key=f"frc{team}",
            )

            q_pts = calculate_qual_pts(rankings=rankings, team_key=f"frc{team}")
            name = event.short_name if len(event.short_name) > 0 else event.name
            rows.append([team, event.key, f"{event.year} {name}", q_pts, a_pts])

    print(make_table(col_names=["Team", "Key", "Event", "Q#", "A#"], row_vals=rows))
