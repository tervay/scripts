from collections import defaultdict
from typing import Callable, Dict, Tuple

import betterproto
import numpy as np
from rich import print
from rich.table import Table

from protos.tpa import Match, Schedule
from py.cli import expose
from py.tpa.context_manager import tpa_cm
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


@expose
async def copr_table(event_key: str, sort_by="rp"):
    table = Table(show_header=True, title=event_key)
    table.add_column("Team", justify="right")
    data = []

    async with tpa_cm() as tpa:
        matches = [m async for m in tpa.get_event_matches(event_key=event_key)]
        teams = set()
        for m in matches:
            for a in [m.alliances.red, m.alliances.blue]:
                teams.update(a.team_keys)

        teams = sorted(list(teams), key=lambda t: int(t[3:]))
        teams = [await tpa.get_team(team_key=t) for t in teams]
        match = matches[35]
        _, sb = betterproto.which_one_of(match, "score_breakdown")
        sb = sb.red.to_dict(
            casing=betterproto.Casing.SNAKE, include_default_values=True
        )

        components = [k for k, v in sb.items() if type(v) in [int, float]]
        sort_index = components.index(sort_by)

        coprs = {}

        def make_copr_fn(component: str) -> Callable:
            def copr_fn(m, c):
                _, sb = betterproto.which_one_of(m, "score_breakdown")
                return getattr(getattr(sb, c), component)

            return copr_fn

        for c in components:
            try:
                coprs[c] = get_component_opr(
                    Schedule(teams=teams, matches=matches), make_copr_fn(c)
                )
                table.add_column(c)
            except:
                print(f"failed on {c}")

        for tk in list(coprs.values())[0]:
            row = [(tk)] + [(round(coprs[c][tk], 2)) for c in components]
            data.append(row)

    data.sort(key=lambda r: -r[sort_index + 1])
    [table.add_row(*[str(c) for c in r]) for r in data]

    print(table)
