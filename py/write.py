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


@expose
def rankings_2013():
    tba = TBA(
        auth_key=key,
        auth_id=auth_id,
        auth_secret=auth_secret,
        event_key="2013iri",
    )

    iri = [
        [1, 1114, 18, 426, 420, 814, 9, 0, 0, 0, 9],
        [2, 2056, 14, 510, 220, 1006, 7, 2, 0, 0, 9],
        [3, 1310, 14, 498, 180, 707, 7, 2, 0, 0, 9],
        [4, 469, 14, 492, 140, 830, 7, 2, 0, 0, 9],
        [5, 868, 14, 474, 220, 932, 7, 2, 0, 0, 9],
        [6, 2648, 14, 450, 230, 767, 7, 2, 0, 0, 9],
        [7, 359, 14, 428, 250, 907, 7, 2, 0, 0, 9],
        [8, 3947, 14, 420, 260, 861, 7, 2, 0, 0, 9],
        [9, 195, 14, 408, 180, 860, 7, 2, 0, 0, 9],
        [10, 67, 14, 402, 310, 840, 7, 2, 0, 0, 9],
        [11, 987, 14, 374, 240, 961, 7, 2, 0, 0, 9],
        [12, 245, 12, 492, 200, 894, 6, 3, 0, 0, 9],
        [13, 33, 12, 480, 190, 860, 6, 3, 0, 0, 9],
        [14, 3928, 12, 468, 210, 784, 6, 3, 0, 0, 9],
        [15, 1538, 12, 444, 290, 812, 6, 3, 0, 0, 9],
        [16, 48, 12, 426, 240, 553, 6, 3, 0, 0, 9],
        [17, 118, 12, 420, 180, 1065, 6, 3, 0, 0, 9],
        [18, 1676, 12, 378, 240, 883, 6, 3, 0, 0, 9],
        [19, 1334, 12, 348, 350, 753, 6, 3, 0, 0, 9],
        [20, 16, 12, 348, 160, 698, 6, 3, 0, 0, 9],
        [21, 11, 11, 358, 210, 727, 5, 3, 1, 0, 9],
        [22, 2468, 10, 444, 180, 745, 5, 4, 0, 0, 9],
        [23, 2590, 10, 420, 220, 846, 5, 4, 0, 0, 9],
        [24, 447, 10, 414, 220, 710, 5, 4, 0, 0, 9],
        [25, 3467, 10, 402, 300, 703, 5, 4, 0, 0, 9],
        [26, 461, 10, 400, 220, 611, 5, 4, 0, 0, 9],
        [27, 4334, 10, 390, 200, 671, 5, 4, 0, 0, 9],
        [28, 68, 10, 378, 200, 516, 5, 4, 0, 0, 9],
        [29, 1625, 9, 432, 200, 752, 4, 4, 1, 0, 9],
        [30, 862, 9, 408, 200, 652, 4, 4, 1, 0, 9],
        [31, 829, 9, 372, 180, 944, 4, 4, 1, 0, 9],
        [32, 624, 8, 474, 200, 818, 4, 5, 0, 0, 9],
        [33, 2474, 8, 474, 200, 643, 4, 5, 0, 0, 9],
        [34, 1741, 8, 438, 250, 791, 4, 5, 0, 0, 9],
        [35, 1732, 8, 432, 200, 695, 4, 5, 0, 0, 9],
        [36, 3476, 8, 430, 220, 701, 4, 5, 0, 0, 9],
        [37, 1477, 8, 402, 230, 819, 4, 5, 0, 0, 9],
        [38, 111, 8, 402, 210, 680, 4, 5, 0, 0, 9],
        [39, 2826, 8, 396, 290, 645, 4, 5, 0, 0, 9],
        [40, 2338, 8, 396, 220, 837, 4, 5, 0, 0, 9],
        [41, 1241, 8, 378, 230, 924, 4, 5, 0, 0, 9],
        [42, 696, 8, 372, 240, 628, 4, 5, 0, 0, 9],
        [43, 3641, 8, 372, 220, 691, 4, 5, 0, 0, 9],
        [44, 27, 8, 372, 190, 743, 4, 5, 0, 0, 9],
        [45, 71, 8, 366, 280, 644, 4, 5, 0, 0, 9],
        [46, 2337, 8, 360, 200, 638, 4, 5, 0, 0, 9],
        [47, 125, 8, 360, 180, 736, 4, 5, 0, 0, 9],
        [48, 4265, 8, 354, 230, 824, 4, 5, 0, 0, 9],
        [49, 2451, 8, 352, 260, 669, 4, 5, 0, 0, 9],
        [50, 4039, 6, 450, 190, 814, 3, 6, 0, 0, 9],
        [51, 45, 6, 420, 180, 497, 3, 6, 0, 0, 9],
        [52, 1592, 6, 408, 170, 766, 3, 6, 0, 0, 9],
        [53, 3847, 6, 402, 230, 736, 3, 6, 0, 0, 9],
        [54, 1640, 6, 390, 250, 688, 3, 6, 0, 0, 9],
        [55, 1024, 6, 360, 230, 673, 3, 6, 0, 0, 9],
        [56, 2175, 6, 358, 190, 672, 3, 6, 0, 0, 9],
        [57, 3539, 6, 356, 170, 682, 3, 6, 0, 0, 9],
        [58, 148, 6, 342, 270, 697, 3, 6, 0, 0, 9],
        [59, 234, 6, 342, 220, 822, 3, 6, 0, 0, 9],
        [60, 116, 6, 342, 170, 655, 3, 6, 0, 0, 9],
        [61, 1902, 6, 294, 220, 644, 3, 6, 0, 0, 9],
        [62, 303, 5, 462, 180, 652, 2, 6, 1, 0, 9],
        [63, 2252, 5, 366, 240, 802, 2, 6, 1, 0, 9],
        [64, 1503, 4, 426, 200, 671, 2, 7, 0, 0, 9],
        [65, 967, 4, 366, 230, 596, 2, 7, 0, 0, 9],
        [66, 20, 4, 346, 220, 577, 2, 7, 0, 0, 9],
        [67, 51, 4, 282, 130, 614, 2, 7, 0, 0, 9],
        [68, 217, 2, 336, 190, 536, 1, 8, 0, 0, 9],
        [69, 4814, 2, 336, 190, 461, 1, 8, 0, 0, 9],
    ]

    to_post = {
        "breakdowns": ["Qual Score", "Auto", "Climb", "Teleop"],
        "rankings": [
            {
                "team_key": f"frc{l[1]}",
                "rank": l[0],
                "wins": l[5 + 1],
                "losses": l[6 + 1],
                "ties": l[7 + 1],
                "played": l[5 + 1] + l[6 + 1] + l[7 + 1],
                "dqs": l[8 + 1],
                "Qual Score": l[2],
                "Auto": l[2 + 1],
                "Climb": l[3 + 1],
                "Teleop": l[4 + 1]
                # "Ranking Score": r.rs,
                # "Avg Match": r.match,
                # "Avg Hangar": r.hangar,
                # "Avg Taxi + Auto Cargo": r.auto,
            }
            for l in iri
        ],
    }

    resp = tba.update_event_rankings(to_post)
    print(resp.status_code)
    pprint(resp.text)


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
