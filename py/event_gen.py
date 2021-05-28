import random
from typing import Dict, List

from colorama import Fore
from protos.tpa import (
    MatchAlliance,
    MatchSimple,
    MatchSimpleAlliances,
    Schedule,
    Team,
    TeamSimple,
)

from py.cli import expose

event_key = "2021fake"


def make_schedule_pb(id_to_team_map: Dict[int, Team], schedule_fp: str) -> Schedule:
    schedule = Schedule(teams=list(id_to_team_map.values()))

    with open(schedule_fp, "r") as f:
        lines = [l.strip().split(",") for l in f.readlines()]

    matches = []
    for match_num, line in enumerate(lines, start=1):
        m = MatchSimple(
            event_key=event_key,
            key=f"{event_key}_qm{match_num}",
            comp_level="qm",
            set_number=1,
            match_number=match_num,
        )

        red_line = line[:6]
        blue_line = line[6:]

        red_alliance = MatchAlliance()
        blue_alliance = MatchAlliance()

        for line, alliance in [(red_line, red_alliance), (blue_line, blue_alliance)]:
            for t_id, is_surrogate in zip(line[::2], line[1::2]):
                alliance.team_keys.append(id_to_team_map[int(t_id)].key)
                if is_surrogate == "1":
                    alliance.surrogate_team_keys.append(id_to_team_map[int(t_id)].key)

        m.alliances = MatchSimpleAlliances(red=red_alliance, blue=blue_alliance)
        matches.append(m)

    schedule.matches = matches
    return schedule


def generate_with_teams(
    team_list: List[TeamSimple], save_path=f"{event_key}.pb", num_matches=10
):
    schedule_filepath = f"schedules/{len(team_list)}_{num_matches}.csv"
    schedule = make_schedule_pb(
        id_to_team_map={
            i: t
            for i, t in enumerate(random.sample(team_list, len(team_list)), start=1)
        },
        schedule_fp=schedule_filepath,
    )

    with open(save_path, "wb+") as f:
        f.write(schedule.SerializeToString())


@expose
def generate(team_list_filepath, save_path=f"{event_key}.pb", num_matches=10):
    with open(team_list_filepath, "r") as f:
        teams = [
            TeamSimple(key=f"frc{t.strip()}", team_number=int(t)) for t in f.readlines()
        ]

    generate_with_teams(teams, save_path=save_path, num_matches=num_matches)


@expose
def pprint_schedule(schedule_pb, highlight=None):
    if "," in str(highlight):
        highlight = highlight.split(",")
    else:
        highlight = [str(highlight)]

    with open(schedule_pb, "rb") as f:
        schedule = Schedule.FromString(f.read())

    for match in schedule.matches:
        out_str = f"{str(match.match_number).rjust(3)}: "
        for k in match.alliances.red.team_keys:
            n = k[3:]
            out_str += Fore.RED if n not in (highlight) else Fore.YELLOW
            out_str += n.rjust(4)
            if k != match.alliances.red.team_keys[-1]:
                out_str += Fore.RESET + "-"

        out_str += Fore.RESET + " vs "
        for k in match.alliances.blue.team_keys:
            n = k[3:]
            out_str += Fore.BLUE if n not in (highlight) else Fore.YELLOW
            out_str += n.rjust(4)
            if k != match.alliances.blue.team_keys[-1]:
                out_str += Fore.RESET + "-"

        out_str += Fore.RESET
        print(out_str)
