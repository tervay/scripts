import datetime

from py.cli import pprint
from py.tba import tba


def flatten_lists(lists):
    return [item for sublist in lists for item in sublist]


async def flatten_lists_async(lists):
    return [item for sublist in lists async for item in sublist]


async def flatten_lists_gen(lists):
    for l in lists:
        async for item in l:
            yield item


def filter_official_events(event_list, allowlist=None):
    blocklist = ["Offseason", "Preseason", "--"]
    if allowlist is None:
        allowlist = []

    return list(
        filter(
            lambda e: e["event_type_string"] not in blocklist
            or e["key"] in allowlist
            or e["event_code"] in allowlist,
            event_list,
        )
    )


def pprint_dict(dictionary, lowest_first=False, index=1, limit=100000000):
    factor = 1 if lowest_first else -1
    pprint(sorted(dictionary.items(), key=lambda t: factor * t[index])[:limit])


def filter_champs_divisions(event_list):
    return list(
        filter(lambda e: e["event_type_string"] == "Championship Division", event_list)
    )


def filter_qual_matches(match_list):
    return list(filter(lambda m: "_qm" in m["key"], match_list))


def filter_bad_matches(match_list):
    return list(filter(lambda m: m["score_breakdown"] is not None, match_list))


def filter_completed_events(event_list):
    return list(filter(is_completed_event, event_list))


def is_completed_event(event) -> bool:
    return (
        datetime.datetime.strptime(event["end_date"], "%Y-%m-%d")
        < datetime.datetime.now()
    )


def sort_matches(match_list):
    return sorted(
        match_list,
        key=lambda m: (
            ["qm", "ef", "qf", "sf", "f"].index(m["comp_level"]),
            m["set_number"],
            m["match_number"],
        ),
    )


def sort_events(event_list):
    return sorted(
        event_list, key=lambda e: (e["year"], 10 if e["week"] is None else e["week"])
    )


def number_to_st_nd_th(n):
    return str(n) + (
        "th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    )


def normalize_bay_numbers(color: str, scorer_table_side: str, sb):
    """
    Normalizes a score breakdown so that bay numbers always have bay1 as the left side and bay 8 as the right side.
    Scorer table side is always from the perspective of red alliance.
    """
    if "_sp_normalized" in sb:
        return sb
    if scorer_table_side == "L":
        if color == "blue":
            auto_new_bays = {}
            tele_new_bays = {}
            for i in [1, 2, 3, 6, 7, 8]:
                auto_new_bays[i] = sb[f"preMatchBay{9 - i}"]
            for i in [1, 2, 3, 4, 5, 6, 7, 8]:
                tele_new_bays[i] = sb[f"bay{9 - i}"]

            for n, data in auto_new_bays.items():
                sb[f"preMatchBay{n}"] = data
            for n, data in tele_new_bays.items():
                sb[f"bay{n}"] = data

    elif scorer_table_side == "R":
        if color == "red":
            auto_new_bays = {}
            tele_new_bays = {}
            for i in [1, 2, 3, 6, 7, 8]:
                auto_new_bays[i] = sb[f"preMatchBay{9 - i}"]
            for i in [1, 2, 3, 4, 5, 6, 7, 8]:
                tele_new_bays[i] = sb[f"bay{9 - i}"]

            for n, data in auto_new_bays.items():
                sb[f"preMatchBay{n}"] = data
            for n, data in tele_new_bays.items():
                sb[f"bay{n}"] = data

    sb["_sp_normalized"] = True
    return sb


def get_teams_in_state(state, year=2019):
    i = 0
    ny_teams = []
    while True:
        page = tba.teams(page=i, year=year)
        if len(page) == 0:
            break

        for team in page:
            if team["state_prov"] == state:
                ny_teams.append(team["team_number"])

        i += 1
    return ny_teams
