from typing import Callable, Dict, Tuple

import numpy as np

from protos.tpa import Match, Schedule
from py.cli import expose
from py.util import OPPOSITE_COLOR, file_cm


def opr_component(m: Match, color: str) -> float:
    return getattr(m.alliances, color).score


def win_lose_rp_component(m: Match, color: str) -> float:
    c_score = getattr(m.alliances, color).score
    opp_score = getattr(m.alliances, OPPOSITE_COLOR[color]).score

    if c_score > opp_score:
        return 2.0
    elif c_score == opp_score:
        return 1.0
    else:
        return 0.0


RP_FNs = {
    2019: (
        lambda m, c: float(
            getattr(m.score_breakdown_2019, c).complete_rocket_ranking_point
        ),
        lambda m, c: float(
            getattr(m.score_breakdown_2019, c).hab_docking_ranking_point
        ),
    ),
    2017: (
        lambda m, c: getattr(m.score_breakdown_2017, c).k_pa_ranking_point_achieved,
        lambda m, c: getattr(m.score_breakdown_2017, c).rotor_ranking_point_achieved,
    ),
}


def get_component_opr(
    schedule: Schedule,
    component_fn: Callable[
        [Match, str],
        float,
    ],
) -> Dict[int, float]:
    teams = schedule.teams
    teams.sort(key=lambda t: t.team_number)
    coprs = {}

    d = {t.team_number: c for c, t in enumerate(teams)}
    b = np.zeros(len(teams))
    a = np.matrix([[0 for _ in range(len(teams))] for _ in range(len(teams))])

    tk_to_team = {t.key: t for t in teams}

    for match in schedule.matches:
        for b1, r1 in zip(
            match.alliances.blue.team_keys, match.alliances.red.team_keys
        ):
            for b2, r2 in zip(
                match.alliances.blue.team_keys, match.alliances.red.team_keys
            ):
                a[
                    (
                        d[tk_to_team[b1].team_number],
                        d[tk_to_team[b2].team_number],
                    )
                ] += 1
                a[
                    (
                        d[tk_to_team[r1].team_number],
                        d[tk_to_team[r2].team_number],
                    )
                ] += 1

            b[d[tk_to_team[b1].team_number]] += component_fn(match, "blue")
            b[d[tk_to_team[r1].team_number]] += component_fn(match, "red")

    coprs = np.linalg.solve(a, b)
    coprs = {t: coprs[i] for t, i in d.items()}
    return coprs
