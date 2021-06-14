import glob
import json
import os
import random
import statistics
from collections import defaultdict
from math import log
from typing import Dict, List

from betterproto import Casing
from colorama import Fore
from tqdm.rich import trange

from protos.tpa import (
    Event,
    FakeEvent,
    MatchAlliance,
    MatchSimple,
    MatchSimpleAlliances,
    Schedule,
    Team,
    TeamSimple,
)
from py.cli import expose
from py.tba import ROOKIE_YEAR_LOWEST_NUMBER, AwardType, EventType
from py.tpa.context_manager import tpa_cm
from py.util import (
    MAX_TEAMS_PAGE_RANGE,
    SHORT_TO_STATE,
    STATE_TO_SHORT,
    chunkify,
    file_cm,
    flatten_lists_async,
    get_real_event_schedule,
    get_savepath,
    sort_events,
    tqdm_bar,
    tqdm_bar_async,
)

save_dir = get_savepath("fake_events")


def make_schedule_pb(
    id_to_team_map: Dict[int, Team], schedule_fp: str, event_key: str
) -> Schedule:
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
    team_list: List[TeamSimple], event_key: str, fname: str, num_matches=10
) -> Schedule:
    schedule_filepath = f"schedules/{len(team_list)}_{num_matches}.csv"
    schedule = make_schedule_pb(
        id_to_team_map={
            i: t
            for i, t in enumerate(random.sample(team_list, len(team_list)), start=1)
        },
        schedule_fp=schedule_filepath,
        event_key=event_key,
    )

    with file_cm(save_dir + "/" + fname, "wb+") as f:
        f.write(schedule.SerializeToString())

    return schedule


@expose
def generate(team_list_filepath, key, num_matches=10):
    with open(team_list_filepath, "r") as f:
        teams = [
            TeamSimple(key=f"frc{t.strip()}", team_number=int(t)) for t in f.readlines()
        ]

    generate_with_teams(teams, key, f"{key}_schedule.pb", num_matches=num_matches)


@expose
def pprint_fe(schedule_pb, highlight=None):
    if "," in str(highlight):
        highlight = highlight.split(",")
    else:
        highlight = [str(highlight)]

    with open(schedule_pb, "rb") as f:
        fake_event = FakeEvent.FromString(f.read())

    for match in fake_event.schedule.matches:
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
    allowlist = set()
    if states is not None:
        allowlist = set(states.split(",")) | set(states.split(", "))
        allowlist = set(STATE_TO_SHORT.get(s.title(), s) for s in allowlist) | set(
            SHORT_TO_STATE.get(s.upper(), s) for s in allowlist
        )

    pts = defaultdict(list)
    cmp_qual = defaultdict(lambda: False)

    async with tpa_cm() as tpa:
        teams = []
        for i in trange(MAX_TEAMS_PAGE_RANGE):
            pg = [t async for t in tpa.get_teams_by_year(year=year, page_num=i)]
            teams.extend(pg)

        for bar, team in tqdm_bar(teams):
            bar.set_description(team.key)
            if (team.state_prov in allowlist) or (states is None):
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

    if states is None:
        states = "all"

    with file_cm(
        get_savepath(f'districts/{states.replace(",", "-")}_{year}.txt'), "w+"
    ) as f:
        for team, team_pts in sorted(pts.items(), key=lambda t: -sum(t[1]))[
            : int(round(n_qualified))
        ]:
            f.write(f"{team[3:]}\n")

    with file_cm(
        get_savepath(f'districts/{states.replace(",", "-")}_{year}_pts.txt'), "w+"
    ) as f:
        for team, team_pts in sorted(pts.items(), key=lambda t: -sum(t[1]))[
            : int(round(n_qualified))
        ]:
            f.write(f"{team[3:]}\t{sum(team_pts)}\n")


@expose
def tba(fake_event_path: str):
    with file_cm(fake_event_path, "rb") as f:
        fake_event = FakeEvent.FromString(f.read())

    with file_cm(
        get_savepath(
            f"fake_events/{fake_event.inner_event.key}/{fake_event.inner_event.key}_tba.json"
        ),
        "w+",
    ) as f:
        d = fake_event.to_dict(casing=Casing.SNAKE)
        d["inner_event"]["playoff_type"] = 0
        d["inner_event"]["parent_event_key"] = None
        d["inner_event"]["division_keys"] = None
        d["inner_event"]["district"] = None
        d["inner_event"]["webcasts"] = {}

        for m in d["schedule"]["matches"]:
            m["score_breakdown"] = None
            m["videos"] = []
            for _, data in m["alliances"].items():
                data["surrogate_team_keys"] = []
                data["dq_team_keys"] = []

        print(
            json.dumps(d, indent=2),
            file=f,
        )


@expose
async def district_from_all(
    year: int, dcmp_fraction: float = 0.35, double_1_events=True
):
    await district_from_states(None, year, dcmp_fraction, double_1_events)


@expose
def create(team_list_filepath):
    get = lambda s: input(f"{s}: ")
    e = Event()

    fields = {
        field: get(field)
        for field in [
            "name",
            "key",
            "city",
        ]
    }

    fields.update(
        {
            "short_name": fields["name"],
            "event_code": fields["key"][4:],
            "event_type": 99,
            "year": int(fields["key"][:4]),
            "timezone": "America/New_York",
            "website": "https://www.thebluealliance.com/",
            "start_date": f'{fields["key"][:4]}-03-01',
            "end_date": f'{fields["key"][:4]}-03-04',
            "location_name": "Fake Arena",
            "state_prov": fields["key"][4:6].upper(),
            "country": "USA",
        }
    )

    for k, v in fields.items():
        setattr(e, k, v)

    print(e)

    with open(team_list_filepath, "r") as f:
        teams = [Team(key=f"frc{t.strip()}", team_number=int(t)) for t in f.readlines()]

    schedule_filepath = f"schedules/{len(teams)}_10.csv"
    schedule = make_schedule_pb(
        id_to_team_map={
            i: t for i, t in enumerate(random.sample(teams, len(teams)), start=1)
        },
        schedule_fp=schedule_filepath,
        event_key=e.key,
    )

    fe = FakeEvent(inner_event=e, schedule=schedule)

    with file_cm(get_savepath(f"fake_events/{e.key}/{e.key}_fe.pb"), "wb+") as f:
        f.write(fe.SerializeToString())


@expose
def divisions(in_fp, n_divs: int, year: int = 2021):
    with file_cm(in_fp, "r") as f:
        lines = f.readlines()

    lines = [int(s.strip()) for s in lines]
    rookies = list(filter(lambda n: n >= ROOKIE_YEAR_LOWEST_NUMBER[year], lines))
    non_rookies = list(filter(lambda n: n < ROOKIE_YEAR_LOWEST_NUMBER[year], lines))

    random.shuffle(rookies)
    random.shuffle(non_rookies)

    split_rookies = [sorted(l) for l in chunkify(rookies, n_divs)]
    split_vets = [sorted(l) for l in chunkify(non_rookies, n_divs)]

    merged = [a + b for a, b in zip(split_vets, split_rookies)]

    files = glob.glob(get_savepath("divs/*"))
    for f in files:
        os.remove(f)

    for i in range(n_divs):
        with file_cm(get_savepath(f"divs/{i + 1}.txt"), "w+") as f:
            for n in merged[i]:
                f.write(f"{n}\n")


@expose
def fair_divisions(in_fp, n_divs: int):
    with file_cm(in_fp, "r") as f:
        lines = f.readlines()

    teams = []
    perfs = {}
    for line in lines:
        tnum, pts = line.strip().split("\t")
        perfs[int(tnum)] = float(pts)
        teams.append(int(tnum))

    eval_limits = {
        "Average": {
            2: 1,
            4: 2,
            8: 2,
        },
        "Distribution": {
            2: 1,
            4: 2.5,
            8: 2.5,
        },
        "Top Distribution": {
            2: 1.5,
            4: 2,
            8: 2,
        },
    }

    def snr(teams: List[int]) -> float:
        x = statistics.mean([perfs[t] for t in teams])
        o = statistics.stdev([perfs[t] for t in teams])

        return 10.0 * log((x * x) / (o * o))

    def top_quartile(teams: List[int]) -> List[int]:
        return sorted(teams, key=lambda t: -perfs[t])[: int(round(len(teams) * 0.25))]

    valid = False
    n = 0
    while not valid:
        random.shuffle(teams)
        divs = [sorted(d) for d in chunkify(teams, n_divs)]
        avgs = []
        dists = []
        top_dists = []

        for div in divs:
            d_avg = statistics.mean([perfs[t] for t in div])
            d_snr = snr(div)
            d_top_snr = snr(top_quartile(div))

            avgs.append(d_avg)
            dists.append(d_snr)
            top_dists.append(d_top_snr)

            if len(avgs) > (n_divs / 2):
                for a in avgs:
                    if abs(a - d_avg) > eval_limits["Average"][n_divs]:
                        break
                else:
                    for d in dists:
                        if abs(d - d_snr) > eval_limits["Distribution"][n_divs]:
                            break
                    else:
                        for td in top_dists:
                            if (
                                abs(td - d_top_snr)
                                > eval_limits["Top Distribution"][n_divs]
                            ):
                                break
                        else:
                            valid = True
        n += 1

    for i in range(n_divs):
        with file_cm(get_savepath(f"divs/{i + 1}.txt"), "w+") as f:
            for n in divs[i]:
                f.write(f"{n}\n")
