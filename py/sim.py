import random
import statistics
from collections import defaultdict

import numpy as np
from rich import print
from tqdm.rich import tqdm

from protos.tpa import (
    FakeAlliance,
    FakeEvent,
    Match,
    MatchAlliance,
    MatchAlliances,
    TeamRp,
    WltRecord,
)
from py.cli import expose
from py.scout import RP_FNs, get_component_opr, opr_component
from py.tpa import SBs
from py.tpa.context_manager import tpa_cm
from py.util import (
    file_cm,
    get_real_event_schedule,
    get_savepath,
    is_official_event,
    tqdm_bar,
)

RP_THRESHOLDS = {
    2019: (0.35, 0.25),
    2018: (0.75, 0.33),
    2017: (0.35, 0.45),
    2016: (1, 1),
    2015: (1, 1),
    2014: (1, 1),
}


@expose
async def sim(fe_fp: str):
    with file_cm(fe_fp, "rb") as f:
        fake_event = FakeEvent.FromString(f.read())

    rankings_file = fe_fp.replace("_fe.pb", "_ranks.tsv")

    schedule = fake_event.schedule
    year = fake_event.inner_event.year

    team_rp1 = defaultdict(list)
    team_rp2 = defaultdict(list)
    team_opr = defaultdict(list)

    rp1_cache = {}
    rp2_cache = {}
    opr_cache = {}

    records = defaultdict(lambda: defaultdict(lambda: 0))
    played = defaultdict(lambda: 0)

    async with tpa_cm() as tpa:
        for bar, team in tqdm_bar(schedule.teams):
            async for event in tpa.get_team_events_by_year(
                year=year, team_key=team.key
            ):
                bar.set_description(event.key.rjust(10))
                if not is_official_event(event):
                    continue

                event_schedule = await get_real_event_schedule(event_key=event.key)
                if event.key not in rp1_cache:
                    try:

                        rp1_coprs = get_component_opr(
                            schedule=event_schedule,
                            component_fn=RP_FNs[year][0],
                        )
                        rp2_coprs = get_component_opr(
                            schedule=event_schedule,
                            component_fn=RP_FNs[year][1],
                        )
                        oprs = get_component_opr(
                            schedule=event_schedule,
                            component_fn=opr_component,
                        )

                        rp1_cache[event.key] = rp1_coprs
                        rp2_cache[event.key] = rp2_coprs
                        opr_cache[event.key] = oprs

                    except np.linalg.LinAlgError:
                        continue

                rp1_coprs = rp1_cache[event.key]
                rp2_coprs = rp2_cache[event.key]
                oprs = opr_cache[event.key]
                try:
                    team_rp1[team.key].append(rp1_coprs[team.team_number])
                    team_rp2[team.key].append(rp2_coprs[team.team_number])
                    team_opr[team.key].append(oprs[team.team_number])
                except KeyError:
                    pass

            for d in [team_rp1, team_rp2, team_opr]:
                if len(d[team.key]) == 0:
                    d[team.key].append(0)

    rps = defaultdict(lambda: 0)
    schedule.matches[0].alliances.red.team_keys
    for m in tqdm(schedule.matches):
        for a in [m.alliances.red, m.alliances.blue]:
            rp1_vars = [statistics.pvariance(team_rp1[k]) for k in a.team_keys]
            rp1_stdev = sum(rp1_vars) ** 0.5
            rp1_means = [statistics.mean(team_rp1[k]) for k in a.team_keys]
            rp1_mean = sum(rp1_means)
            if (n := random.gauss(rp1_mean, rp1_stdev)) > RP_THRESHOLDS[year][0]:
                # print(f"Awarding RP1 as n={round(n,2)} to {a.team_keys}")
                for k in a.team_keys:
                    rps[k] += 1

            rp2_vars = [statistics.pvariance(team_rp2[k]) for k in a.team_keys]
            rp2_stdev = sum(rp2_vars) ** 0.5
            rp2_means = [statistics.mean(team_rp2[k]) for k in a.team_keys]
            rp2_mean = sum(rp2_means)
            if (n := random.gauss(rp2_mean, rp2_stdev)) > RP_THRESHOLDS[year][1]:
                # print(f"Awarding RP2 as n={round(n,2)} to {a.team_keys}")
                for k in a.team_keys:
                    rps[k] += 1

        red_pt_vars = [
            statistics.pvariance(team_opr[k]) for k in m.alliances.red.team_keys
        ]
        red_pt_stdev = sum(red_pt_vars) ** 0.5
        red_pt_means = [statistics.mean(team_opr[k]) for k in m.alliances.red.team_keys]
        red_pt_mean = sum(red_pt_means)
        red_pts = round(random.gauss(red_pt_mean, red_pt_stdev))

        blue_pt_vars = [
            statistics.pvariance(team_opr[k]) for k in m.alliances.blue.team_keys
        ]
        blue_pt_stdev = sum(blue_pt_vars) ** 0.5
        blue_pt_means = [
            statistics.mean(team_opr[k]) for k in m.alliances.blue.team_keys
        ]
        blue_pt_mean = sum(blue_pt_means)
        blue_pts = round(random.gauss(blue_pt_mean, blue_pt_stdev))

        m.alliances.blue.score = blue_pts
        m.alliances.red.score = red_pts

        if red_pts > blue_pts:
            for k in m.alliances.red.team_keys:
                rps[k] += 2
                records[k]["wins"] += 1
        elif red_pts == blue_pts:
            for a in [m.alliances.red, m.alliances.blue]:
                for k in a.team_keys:
                    rps[k] += 1
                    records[k]["ties"] += 1
        else:
            for k in m.alliances.blue.team_keys:
                rps[k] += 2
                records[k]["wins"] += 1

        for a in [m.alliances.red, m.alliances.blue]:
            for k in a.team_keys:
                played[k] += 1

    for t, rec in records.items():
        rec["losses"] = played[t] - (rec["wins"] + rec["ties"])

    with file_cm(rankings_file, "w+") as f:
        async with tpa_cm() as tpa:
            for bar, (k, rp) in tqdm_bar(sorted(rps.items(), key=lambda t: -t[1])):
                bar.set_description(k)
                team = await tpa.get_team(team_key=k)
                f.write(f"{team.team_number}\t{team.nickname}\n")

    with file_cm(fe_fp, "wb+") as f:
        fake_event.schedule = schedule
        async with tpa_cm() as tpa:
            for k, rp in sorted(rps.items(), key=lambda t: -t[1]):
                team = await tpa.get_team(team_key=k)
                fake_event.rankings.append(
                    TeamRp(team=team, rp=rp, record=WltRecord().from_dict(records[k]))
                )

        f.write(fake_event.SerializeToString())


@expose
def print_faked_schedule(path):
    with file_cm(path, "rb") as f:
        fake_event = FakeEvent.FromString(f.read())

    print(fake_event.schedule.matches[1])


@expose
async def save_draft(fake_event_path: str):
    with file_cm(fake_event_path, "rb") as f:
        fake_event = FakeEvent.FromString(f.read())

    print(f"Alliances: (ctrl-d to end)")
    alliances_raw = []
    try:
        while True:
            alliances_raw.append(input())
    except EOFError:
        pass

    fake_event.alliance_selection.clear()
    fake_event.schedule.matches = list(
        filter(lambda m: m.comp_level == "qm", fake_event.schedule.matches)
    )

    async with tpa_cm() as tpa:
        for i, raw_alliance in enumerate(alliances_raw, start=1):
            c, p1, p2 = raw_alliance.split("\t")
            fake_event.alliance_selection.append(
                FakeAlliance(
                    captain=await tpa.get_team(team_key=f"frc{c}"),
                    first_pick=await tpa.get_team(team_key=f"frc{p1}"),
                    second_pick=await tpa.get_team(team_key=f"frc{p2}"),
                    seed=i,
                )
            )

    def gen_fake_elim_match(
        event_key: str,
        comp_level: str,
        set_number: int,
        match_number: int,
        red_fake: FakeAlliance,
        blue_fake: FakeAlliance,
        red_score: int,
        blue_score: int,
    ) -> Match:
        return Match(
            alliances=MatchAlliances(
                red=MatchAlliance(
                    score=red_score,
                    team_keys=[
                        red_fake.first_pick.key,
                        red_fake.captain.key,
                        red_fake.second_pick.key,
                    ],
                ),
                blue=MatchAlliance(
                    score=blue_score,
                    team_keys=[
                        blue_fake.first_pick.key,
                        blue_fake.captain.key,
                        blue_fake.second_pick.key,
                    ],
                ),
            ),
            key=f"{event_key}_{comp_level}{set_number}m{match_number}",
            comp_level=comp_level,
            set_number=set_number,
            match_number=match_number,
            winning_alliance="red" if red_score > blue_score else "blue",
            event_key=event_key,
        )

    # Qf
    a = lambda n: fake_event.alliance_selection[n - 1]
    sa = lambda a_: f"{a_.captain.key}-{a_.first_pick.key}-{a_.second_pick.key}"
    qf18_winner = int(input(f"1. [{sa(a(1))}] vs 8. [{sa(a(8))}] - "))
    fake_event.schedule.matches.extend(
        [
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=1,
                match_number=1,
                red_fake=a(1),
                blue_fake=a(8),
                red_score=2 if qf18_winner == 1 else 1,
                blue_score=1 if qf18_winner == 1 else 2,
            ),
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=1,
                match_number=2,
                red_fake=a(1),
                blue_fake=a(8),
                red_score=2 if qf18_winner == 1 else 1,
                blue_score=1 if qf18_winner == 1 else 2,
            ),
        ]
    )

    qf27_winner = int(input(f"2. [{sa(a(2))}] vs 7. [{sa(a(7))}] - "))
    fake_event.schedule.matches.extend(
        [
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=3,
                match_number=1,
                red_fake=a(2),
                blue_fake=a(7),
                red_score=2 if qf27_winner == 2 else 1,
                blue_score=1 if qf27_winner == 2 else 2,
            ),
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=3,
                match_number=2,
                red_fake=a(2),
                blue_fake=a(7),
                red_score=2 if qf27_winner == 2 else 1,
                blue_score=1 if qf27_winner == 2 else 2,
            ),
        ]
    )

    qf36_winner = int(input(f"3. [{sa(a(3))}] vs 6. [{sa(a(6))}] - "))
    fake_event.schedule.matches.extend(
        [
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=4,
                match_number=1,
                red_fake=a(3),
                blue_fake=a(6),
                red_score=2 if qf36_winner == 3 else 1,
                blue_score=1 if qf36_winner == 3 else 2,
            ),
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=4,
                match_number=2,
                red_fake=a(3),
                blue_fake=a(6),
                red_score=2 if qf36_winner == 3 else 1,
                blue_score=1 if qf36_winner == 3 else 2,
            ),
        ]
    )

    qf45_winner = int(input(f"4. [{sa(a(4))}] vs 5. [{sa(a(5))}] - "))
    fake_event.schedule.matches.extend(
        [
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=2,
                match_number=1,
                red_fake=a(4),
                blue_fake=a(5),
                red_score=2 if qf45_winner == 4 else 1,
                blue_score=1 if qf45_winner == 4 else 2,
            ),
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="qf",
                set_number=2,
                match_number=2,
                red_fake=a(4),
                blue_fake=a(5),
                red_score=2 if qf45_winner == 4 else 1,
                blue_score=1 if qf45_winner == 4 else 2,
            ),
        ]
    )

    # Sf
    sf14_winner = int(
        input(
            f"{qf18_winner}. [{sa(a(qf18_winner))}] vs {qf45_winner}. [{sa(a(qf45_winner))}] - "
        )
    )
    fake_event.schedule.matches.extend(
        [
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="sf",
                set_number=1,
                match_number=1,
                red_fake=a(qf18_winner),
                blue_fake=a(qf45_winner),
                red_score=2 if sf14_winner == qf18_winner else 1,
                blue_score=1 if sf14_winner == qf18_winner else 2,
            ),
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="sf",
                set_number=1,
                match_number=2,
                red_fake=a(qf18_winner),
                blue_fake=a(qf45_winner),
                red_score=2 if sf14_winner == qf18_winner else 1,
                blue_score=1 if sf14_winner == qf18_winner else 2,
            ),
        ]
    )

    sf23_winner = int(
        input(
            f"{qf27_winner}. [{sa(a(qf27_winner))}] vs {qf36_winner}. [{sa(a(qf36_winner))}] - "
        )
    )
    fake_event.schedule.matches.extend(
        [
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="sf",
                set_number=2,
                match_number=1,
                red_fake=a(qf27_winner),
                blue_fake=a(qf36_winner),
                red_score=2 if sf23_winner == qf27_winner else 1,
                blue_score=1 if sf23_winner == qf27_winner else 2,
            ),
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="sf",
                set_number=2,
                match_number=2,
                red_fake=a(qf27_winner),
                blue_fake=a(qf36_winner),
                red_score=2 if sf23_winner == qf27_winner else 1,
                blue_score=1 if sf23_winner == qf27_winner else 2,
            ),
        ]
    )

    # F
    f_winner = int(
        input(
            f"{sf14_winner}. [{sa(a(sf14_winner))}] vs {sf23_winner}. [{sa(a(sf23_winner))}] - "
        )
    )
    fake_event.schedule.matches.extend(
        [
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="f",
                set_number=1,
                match_number=1,
                red_fake=a(sf14_winner),
                blue_fake=a(sf23_winner),
                red_score=2 if f_winner == sf14_winner else 1,
                blue_score=1 if f_winner == sf14_winner else 2,
            ),
            gen_fake_elim_match(
                event_key=fake_event.inner_event.key,
                comp_level="f",
                set_number=1,
                match_number=2,
                red_fake=a(sf14_winner),
                blue_fake=a(sf23_winner),
                red_score=2 if f_winner == sf14_winner else 1,
                blue_score=1 if f_winner == sf14_winner else 2,
            ),
        ]
    )

    with file_cm(fake_event_path, "wb+") as f:
        f.write(fake_event.SerializeToString())
