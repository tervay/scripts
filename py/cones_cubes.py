from tbapy import TBA
import numpy as np
from pprint import pprint
from collections import defaultdict
from tqdm import tqdm

tba = TBA("1EhUOwczJi4vDUXza94fAo7s4UFrKgBrTJ6A3MTeYR0WrgzlyGR0Tzyl1TN2P6Tu")
event_key = "2023isde1"


class Accessors:
    def high_cones(match, color):
        return match["score_breakdown"][color]["autoCommunity"]["T"].count(
            "Cone"
        ) + match["score_breakdown"][color]["teleopCommunity"]["T"].count("Cone")

    def mid_cones(match, color):
        return match["score_breakdown"][color]["autoCommunity"]["M"].count(
            "Cone"
        ) + match["score_breakdown"][color]["teleopCommunity"]["M"].count("Cone")

    def low_cones(match, color):
        return match["score_breakdown"][color]["autoCommunity"]["B"].count(
            "Cone"
        ) + match["score_breakdown"][color]["teleopCommunity"]["B"].count("Cone")

    def high_cubes(match, color):
        return match["score_breakdown"][color]["autoCommunity"]["T"].count(
            "Cube"
        ) + match["score_breakdown"][color]["teleopCommunity"]["T"].count("Cube")

    def mid_cubes(match, color):
        return match["score_breakdown"][color]["autoCommunity"]["M"].count(
            "Cube"
        ) + match["score_breakdown"][color]["teleopCommunity"]["M"].count("Cube")

    def low_cubes(match, color):
        return match["score_breakdown"][color]["autoCommunity"]["B"].count(
            "Cube"
        ) + match["score_breakdown"][color]["teleopCommunity"]["B"].count("Cube")

    def cones(match, color):
        return sum(
            [
                Accessors.high_cones(match, color),
                Accessors.mid_cones(match, color),
                Accessors.low_cones(match, color),
            ]
        )

    def cubes(match, color):
        return sum(
            [
                Accessors.high_cubes(match, color),
                Accessors.mid_cubes(match, color),
                Accessors.low_cubes(match, color),
            ]
        )

    def default_accessor(component):
        return lambda match, color: float(
            match["score_breakdown"][color].get(component, 0)
        )


def build_team_mapping(matches):
    team_set = set()
    for match in matches:
        for color in ["red", "blue"]:
            for team in match["alliances"][color]["team_keys"]:
                team_set.add(team[3:])

    team_list = list(team_set)
    team_id_map = {}
    for i, team in enumerate(team_list):
        team_id_map[team] = i

    return team_list, team_id_map


def build_s_matrix(matches, team_id_map, accessor):
    n = len(team_id_map.keys())
    s = np.zeros((n, 1))
    for match in matches:
        if match["alliances"]["blue"]["score"] == -1:
            continue

        for color in ["red", "blue"]:
            alliance_teams = [
                team[3:] for team in match["alliances"][color]["team_keys"]
            ]
            stat = accessor(match, color)
            for team in alliance_teams:
                s[team_id_map[team]] += stat

    return s


def calc_stat(matches, team_list, team_id_map, m_inv, accessor):
    s = build_s_matrix(matches, team_id_map, accessor)
    x = np.dot(m_inv, s)
    stat_dict = {}
    for team, stat in zip(team_list, x):
        stat_dict[team] = stat[0]

    return stat_dict


def build_m_inv_matrix(matches, team_id_map):
    n = len(team_id_map.keys())
    M = np.zeros((n, n))
    for match in matches:
        if match["alliances"]["blue"]["score"] == -1:
            continue

        for color in ["red", "blue"]:
            alliance_teams = match["alliances"][color]["team_keys"]
            for team1 in alliance_teams:
                for team2 in alliance_teams:
                    M[team_id_map[team1[3:]], team_id_map[team2[3:]]] += 1

    return np.linalg.pinv(M)


def opr(matches):
    team_list, team_id_map = build_team_mapping(matches)
    if not team_list:
        return {}

    m_inv = build_m_inv_matrix(matches, team_id_map)
    oprs = calc_stat(
        matches, team_list, team_id_map, m_inv, lambda m, c: m["alliances"][c]["score"]
    )
    return oprs


def accessor(matches, accessor):
    team_list, team_id_map = build_team_mapping(matches)
    if not team_list:
        return {}

    m_inv = build_m_inv_matrix(matches, team_id_map)
    oprs = calc_stat(matches, team_list, team_id_map, m_inv, accessor)
    return oprs


print_headers = True

for event in tqdm(tba.events(year=2023)):
    if event["week"] is None or event["week"] >= 4:
        continue

    matches = tba.event_matches(event=event["key"])
    if len(matches) == 0:
        continue

    if matches[0]["score_breakdown"] is None:
        continue

    team_rows = defaultdict(list)
    headers = ["team", "eventKey", "week"]
    for accessor_fn in [
        Accessors.cones,
        Accessors.high_cones,
        Accessors.mid_cones,
        Accessors.low_cones,
        Accessors.cubes,
        Accessors.high_cubes,
        Accessors.mid_cubes,
        Accessors.low_cubes,
    ]:
        for team, copr in accessor(matches, accessor=accessor_fn).items():
            team_rows[team].append(round(copr, 4))

        headers.append(accessor_fn.__name__)

    for component, value in matches[0]["score_breakdown"]["red"].items():
        try:
            float(value)
        except (ValueError, TypeError):
            continue
        else:
            for team, copr in accessor(
                matches, accessor=Accessors.default_accessor(component)
            ).items():
                team_rows[team].append(round(copr, 4))

            headers.append(component)

    if print_headers:
        print(",".join(headers))
        print_headers = False

    for team, row in team_rows.items():
        print(",".join([str(x) for x in [team, event["key"], event["week"] + 1] + row]))
