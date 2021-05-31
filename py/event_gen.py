import random
from collections import defaultdict
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

from py.cli import expose, pprint
from py.tba import AwardType, EventType
from py.tpa.context_manager import tpa_cm
from py.util import (
    MAX_TEAMS_PAGE_NUM,
    file_cm,
    flatten_lists_async,
    get_real_event_schedule,
    get_savepath,
    sort_events,
    tqdm_bar_async,
)

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


def generate_with_teams(team_list: List[TeamSimple], fname: str, num_matches=10):
    schedule_filepath = f"schedules/{len(team_list)}_{num_matches}.csv"
    schedule = make_schedule_pb(
        id_to_team_map={
            i: t
            for i, t in enumerate(random.sample(team_list, len(team_list)), start=1)
        },
        schedule_fp=schedule_filepath,
    )

    with file_cm(get_savepath(fname), "wb+") as f:
        f.write(schedule.SerializeToString())


@expose
def generate(team_list_filepath, fname=f"{event_key}_schedule.pb", num_matches=10):
    with open(team_list_filepath, "r") as f:
        teams = [
            TeamSimple(key=f"frc{t.strip()}", team_number=int(t)) for t in f.readlines()
        ]

    generate_with_teams(teams, fname=fname, num_matches=num_matches)


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


@expose
async def save_real_schedule(event_key, fname=None):
    if fname is None:
        fname = f"{event_key}.pb"

    with file_cm(get_savepath(fname), "wb+") as f:
        f.write(
            (await get_real_event_schedule(event_key=event_key)).SerializeToString()
        )


@expose
async def district_from_states(
    states: str, year: int, dcmp_fraction: float = 0.35, double_1_events=True
):
    states = states.title()
    allowlist = set(states.split(",")) | set(states.split(", "))

    pts = defaultdict(list)
    cmp_qual = defaultdict(lambda: False)

    async with tpa_cm() as tpa:
        async for bar, team in tqdm_bar_async(
            await flatten_lists_async(
                [
                    tpa.get_teams_by_year(year=year, page_num=i)
                    for i in range(MAX_TEAMS_PAGE_NUM)
                ]
            )
        ):
            bar.set_description(team.key)
            if team.state_prov in allowlist:
                events = [
                    e
                    async for e in tpa.get_team_events_by_year(
                        team_key=team.key, year=year
                    )
                ]
                if any([e.event_type in EventType.CMP_EVENT_TYPES for e in events]):
                    cmp_qual[team.key] = True

                for e in events:
                    async for award in tpa.get_team_event_awards(
                        team_key=team.key, event_key=e.key
                    ):
                        if (
                            award.award_type in AwardType.CMP_QUALIFYING_AWARDS
                            and e.event_type == EventType.REGIONAL
                        ):
                            cmp_qual[team.key] = True

                events = [
                    e for e in events if e.event_type in EventType.NON_CMP_EVENT_TYPES
                ]
                events = sort_events(events)

                n = 0
                for event in events:
                    if n == 2:
                        break

                    dpts = await tpa.get_event_district_points(event_key=event.key)
                    if team.key not in dpts.points:
                        continue

                    pts[team.key].append(dpts.points[team.key].total)
                    n += 1

                if team.key in pts and len(pts[team.key]) == 1 and double_1_events:
                    pts[team.key].append(pts[team.key][0])

                if team.rookie_year == year:
                    pts[team.key].append(10)
                elif team.rookie_year == year - 1:
                    pts[team.key].append(5)

    n_qualified = dcmp_fraction * len(pts.keys())
    for i, (team, team_pts) in enumerate(
        sorted(pts.items(), key=lambda t: -sum(t[1])), start=1
    ):
        team_color = Fore.GREEN if i < n_qualified else Fore.RED

        pts_str = [str(p).rjust(2) for p in team_pts]
        pts_str = " + ".join(pts_str).ljust(12)
        cmp_str = f"{Fore.GREEN}✓" if cmp_qual[team] else ""

        print(
            f"{Fore.RESET}{str(i).rjust(3)}. {team_color}{team[3:].rjust(4)}{Fore.RESET} "
            + f"{pts_str} = {sum(team_pts)}\t{cmp_str}"
        )
