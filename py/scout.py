from typing import Callable, Dict

import betterproto
import numpy as np
from rich import print
from rich.pretty import pprint
from rich.table import Table
from scipy import optimize

from protos.tpa import Match, Schedule
from py.cli import expose
from py.tpa.context_manager import tpa_cm
from py.util import OPPOSITE_COLOR, OPRUtils, make_table, make_table_from_dict
from scipy.optimize import minimize


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


@expose
async def opr(event_key: str):
    async with tpa_cm() as tpa:
        team_to_indx = {
            t.key: i
            for i, t in enumerate(
                [t async for t in tpa.get_event_teams(event_key=event_key)]
            )
        }
        indx_to_team = {v: k for k, v in team_to_indx.items()}
        matches = [
            m
            async for m in tpa.get_event_matches(event_key=event_key)
            if m.comp_level == "qm"
        ]

        def individual_match_error(x, m_number: int) -> float:
            ret = 0
            for alliance in [
                matches[m_number].alliances.blue,
                matches[m_number].alliances.red,
            ]:
                predicted_score = 0
                for tk in alliance.team_keys:
                    predicted_score += x[team_to_indx[tk]]

                ret += abs(alliance.score - predicted_score)

            return ret

        def score_fn(x):
            return sum([individual_match_error(x, i) for i in range(len(matches))])

        x0 = [0 for _ in range(len(team_to_indx.keys()))]
        lower_bounds = [0 for _ in range(len(team_to_indx.keys()))]
        upper_bounds = [200 for _ in range(len(team_to_indx.keys()))]
        bounds = optimize.Bounds(lower_bounds, upper_bounds)
        res = optimize.minimize(
            score_fn, x0, method="trust-constr", bounds=bounds, options={"disp": True}
        )

        oprs = {indx_to_team[i]: x for i, x in enumerate(res.x)}
        print(make_table_from_dict(oprs, round_to=2))


class optim_dict:
    def __init__(self):
        self.var_dict = {}

    def __len__(self):
        return len(self.var_dict.keys())

    class optim_var:
        def __init__(self, var):
            self.var = var
            self.shape = var.shape

    def add_var(self, var_name, var):
        """
        Parameters:
        var_name (string): Key name of the variable
        var (np.array): N-D np.array of variable contents
        """
        self.var_dict[var_name] = self.optim_var(var)

    def toVector(self):
        """
        Returns:
        1-D np.array: Compresses contents of self.optim_dict into 1-D np.array required by Scipy Minimize
        """
        return np.hstack(
            [optim_var.var.flatten() for optim_var in self.var_dict.values()]
        )

    def toDict(self, x):
        """
        Parameters:
        x (1D np.array): Inputs to Scipy Minimize
        Returns:
        dictionary: Summarizes 1-D np.array from Scipy Minimize input into dictionary class with variables
            accessible by name
        """

        def tuple_product(t):
            """
            Parameters:
            t (tuple)
            Returns:
            int: product of all elements in the tuple
            """
            res = 1
            for x in t:
                res *= x
            return res

        return_dict = {}
        start_index = 0
        for var_name in self.var_dict.keys():
            var_shape = self.var_dict[var_name].shape
            end_index = start_index + tuple_product(var_shape)

            return_dict[var_name] = x[start_index:end_index].reshape(var_shape)
            start_index = end_index

        return


@expose
async def better_opr(event_key: str):
    async with tpa_cm() as tpa:
        matches = [m async for m in tpa.get_event_matches(event_key=event_key)]
        
        def fn(x):
            pass


