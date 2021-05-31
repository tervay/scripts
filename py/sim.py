import random
import statistics
from collections import defaultdict

import numpy as np
from tqdm import tqdm

from protos.tpa import Schedule
from py.cli import expose
from py.scout import RP_FNs, get_component_opr, opr_component
from py.tpa.context_manager import tpa_cm
from py.util import file_cm, get_real_event_schedule, is_official_event, tqdm_bar

RP_THRESHOLDS = {
    2019: (0.5, 1),
    2018: (1, 1),
    2017: (1, 1),
    2016: (1, 1),
    2015: (1, 1),
    2014: (1, 1),
}


@expose
async def sim(schedule_fp, year, outfile=None):
    if outfile is None:
        outfile = f"{schedule_fp}_simmed_for_{year}.txt"

    with file_cm(schedule_fp, "rb") as f:
        schedule = Schedule.FromString(f.read())

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
                for k in a.team_keys:
                    rps[k] += 1

            rp2_vars = [statistics.pvariance(team_rp2[k]) for k in a.team_keys]
            rp2_stdev = sum(rp2_vars) ** 0.5
            rp2_means = [statistics.mean(team_rp2[k]) for k in a.team_keys]
            rp2_mean = sum(rp2_means)
            if (n := random.gauss(rp2_mean, rp2_stdev)) > RP_THRESHOLDS[year][1]:
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

    def rec_str(rec):
        return f'{rec["wins"]}-{rec["losses"]}-{rec["ties"]}'

    for i, (k, rp) in enumerate(sorted(rps.items(), key=lambda t: -t[1]), start=1):
        print(f"{str(i).rjust(3)}. {k.rjust(3 + 4)} - {rp} - {rec_str(records[k])}")

    with file_cm(outfile, "w+") as f:
        async with tpa_cm() as tpa:
            for bar, (k, rp) in tqdm_bar(sorted(rps.items(), key=lambda t: -t[1])):
                bar.set_description(k)
                team = await tpa.get_team(team_key=k)
                print(f"{team.team_number}\t{team.nickname}", file=f)
