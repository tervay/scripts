from pprint import pprint
from typing import List

from py.cli import expose
from py.data.writes import (
    BOTB2022,
    ILRR2022,
    INRA2022,
    NERD2022,
    ONSC2022,
    Battlecry2021Saturday,
    Battlecry2021Sunday,
    Battlecry2022Eighthfinals,
    DoubleElimMatchResult,
    FMatchResult,
    GovCup2022,
    MayhemInMerrimack2022,
    RRMatchResult,
    Ranking2022,
    RiverRage2021,
    Ruckus2022,
    SummerHeat2022,
)
from py.multiproc.mp import FnArgs, call, sum_
from collections import namedtuple

from key import key, auth_secret, auth_id
from tbapy import TBA


@expose
def set_custom(event_key: str):
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key=event_key,
    )
    resp = tba.update_event_info({"playoff_type": 10})
    print(resp.status_code)
    pprint(resp.text)


@expose
def round_robin(event_key: str):
    write_rr_helper(
        event_key=event_key,
        rr_results={
            "2021bc1": Battlecry2021Saturday.rr_results,
            "2021bc2": Battlecry2021Sunday.rr_results,
            "2021nhrr": RiverRage2021.rr_results,
            "2022mesh": SummerHeat2022.rr_results,
            "2022bc": Battlecry2022Eighthfinals.rr_results,
            "2022nhmm": MayhemInMerrimack2022.rr_results,
        }[event_key],
        f_results={
            "2021bc1": Battlecry2021Saturday.f_results,
            "2021bc2": Battlecry2021Sunday.f_results,
            "2021nhrr": RiverRage2021.f_results,
            "2022mesh": SummerHeat2022.f_results,
            "2022bc": [],
            "2022nhmm": MayhemInMerrimack2022.f_results,
        }[event_key],
    )


def write_rr_helper(
    event_key: str, rr_results: List[RRMatchResult], f_results: List[FMatchResult]
):
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key=event_key,
    )

    to_post = [
        {
            "comp_level": "sf",
            "set_number": 1,
            "match_number": r.num,
            "alliances": {
                "red": {
                    "teams": [f"frc{k}" for k in r.red],
                    "score": r.red_score,
                    "surrogates": [],
                    "dqs": [],
                },
                "blue": {
                    "teams": [f"frc{k}" for k in r.blue],
                    "score": r.blue_score,
                    "surrogates": [],
                    "dqs": [],
                },
            },
            "score_breakdown": None,
            "time_str": None,
            "time_utc": None,
        }
        for r in rr_results
    ] + [
        {
            "comp_level": "f",
            "set_number": 1,
            "match_number": r.num,
            "alliances": {
                "red": {
                    "teams": [f"frc{k}" for k in r.red],
                    "score": r.red_score,
                    "surrogates": [],
                    "dqs": [],
                },
                "blue": {
                    "teams": [f"frc{k}" for k in r.blue],
                    "score": r.blue_score,
                    "surrogates": [],
                    "dqs": [],
                },
            },
            "score_breakdown": None,
            "time_str": None,
            "time_utc": None,
        }
        for r in f_results
    ]

    resp = tba.update_event_matches(to_post)
    print(resp.status_code)
    pprint(resp.text)


@expose
def rankings(event_key: str):
    rankings_helper(
        event_key=event_key,
        rankings={
            "2022mesh": SummerHeat2022.rankings,
            "2022nhmm": MayhemInMerrimack2022.rankings,
            "2022nhgc": GovCup2022.rankings,
            "2022mabil": NERD2022.rankings,
            "2022nhbb": BOTB2022.rankings,
            "2022nyrr": Ruckus2022.rankings,
            "2022inra": INRA2022.rankings,
            "2022ilrr": ILRR2022.rankings,
        }[event_key],
    )


def rankings_helper(event_key: str, rankings: List[Ranking2022]):
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key=event_key,
    )

    to_post = {
        "breakdowns": [
            "Ranking Score",
            "Avg Match",
            "Avg Hangar",
            "Avg Taxi + Auto Cargo",
        ],
        "rankings": [
            {
                "team_key": f"frc{r.team}",
                "rank": i,
                "wins": r.wins,
                "losses": r.losses,
                "ties": r.ties,
                "played": r.wins + r.losses + r.ties,
                "dqs": r.dq,
                "Ranking Score": r.rs,
                "Avg Match": r.match,
                "Avg Hangar": r.hangar,
                "Avg Taxi + Auto Cargo": r.auto,
            }
            for i, r in enumerate(rankings, start=1)
        ],
    }

    resp = tba.update_event_rankings(to_post)
    print(resp.status_code)
    pprint(resp.text)


@expose
def delete():
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key="2021bc1",
    )
    resp = tba.delete_event_matches([f"f1m{n}" for n in range(4, 16)])
    print(resp.status_code)
    pprint(resp.text)


@expose
def alliances():
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key="2022bc",
    )
    f = lambda teams: [f"frc{t}" for t in teams]
    resp = tba.update_event_alliances(
        [
            f([2168, 7407, 2265, 3182]),  # 1
            f([88, 6328, 1991]),  # 2
            f([1468, 238, 5494, 1735]),  # 3
            f([131, 3467, 2423, 6324]),  # 4
            f([5813, 195, 716, 467]),  # 5
            f([8544, 1100, 121, 1155]),  # 6
            f([4909, 694, 126, 839]),  # 7
            f([48, 1768, 1740, 190]),  # 8
            f([78, 319, 7153, 173]),  # 9
            f([175, 8085, 157]),  # 10
            f([177, 228, 4122, 7462]),  # 11
            f([1073, 2370, 4041, 8567]),  # 12
            f([2877, 1796, 501]),  # 13
            f([2084, 2713, 2262, 155]),  # 14
            f([8724, 1058, 4048, 6763]),  # 15
            f([1474, 166, 1729, 138]),  # 16
        ]
    )
    print(resp.status_code)
    pprint(resp.text)


@expose
def remap_teams(event_key: str):
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key=event_key,
    )

    resp = tba.update_event_info(
        {
            "remap_teams": {
                "2022nhgc": GovCup2022.remap_teams,
                "2022nhmm": MayhemInMerrimack2022.remap_teams,
                "2022mesh": SummerHeat2022.remap_teams,
                "2022mabil": NERD2022.remap_teams,
            }[event_key]
        }
    )
    print(resp.status_code)
    print(resp.text)


@expose
def double_elim(event_key: str):
    double_elim_helper(
        event_key=event_key,
        double_elim_matches={
            "2022onsc": ONSC2022.double_elim_results,
        }[event_key],
    )


def double_elim_helper(
    event_key: str, double_elim_matches: List[DoubleElimMatchResult]
):
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key=event_key,
    )
    resp = tba.update_event_matches(
        [
            {
                "comp_level": match.comp_level,
                "set_number": match.set_number,
                "match_number": match.match_number,
                "alliances": {
                    "red": {
                        "teams": [f"frc{k}" for k in match.red],
                        "score": match.red_score,
                        "surrogates": [],
                        "dqs": [],
                    },
                    "blue": {
                        "teams": [f"frc{k}" for k in match.blue],
                        "score": match.blue_score,
                        "surrogates": [],
                        "dqs": [],
                    },
                },
                "score_breakdown": None,
                "time_str": None,
                "time_utc": None,
            }
            for match in double_elim_matches
        ]
    )
    print(resp.status_code)
    print(resp.text)
