from collections import defaultdict
from itertools import combinations
from typing import List

from rich import print
from tqdm.rich import tqdm, trange

from protos.tpa import EliminationAlliance
from py.cli import expose
from py.tba import EventType
from py.tpa import tpa_cm
from py.util import file_cm, get_savepath, tqdm_bar


def elim_perms(seeds, n, disallowed):
    perms = list(combinations(seeds, n))
    for d in disallowed:
        perms = list(filter(lambda p: not (d[0] in p and d[1] in p), perms))

    return list(perms)


def elim_str(alliances: List[EliminationAlliance], event_key: str) -> str:
    s = ""
    s += "1" if alliances[7].status.level == "qf" else "8"
    s += "2" if alliances[6].status.level == "qf" else "7"
    s += "3" if alliances[5].status.level == "qf" else "6"
    s += "4" if alliances[4].status.level == "qf" else "5"

    s = "".join([str(c) for c in sorted([int(c) for c in s])])

    s += "_"

    sf_s = []
    for i, a in enumerate(alliances, start=1):
        if a.status.level == "sf":
            for opp in {
                1: [4, 5],
                8: [4, 5],
                2: [3, 6],
                7: [3, 6],
                3: [2, 7],
                6: [2, 7],
                4: [1, 8],
                5: [1, 8],
            }[i]:
                if alliances[opp - 1].status.level == "f":
                    sf_s.append(opp)

    s += "".join([str(c) for c in sorted(sf_s)])

    s += "_"
    for i, a in enumerate(alliances, start=1):
        if a.status.status == "won":
            s += str(i)

    return s


@expose
async def bracket_counts():
    counts = {}
    qf_perms = elim_perms([1, 2, 3, 4, 5, 6, 7, 8], 4, [(1, 8), (2, 7), (3, 6), (4, 5)])
    for qfp in qf_perms:
        qfs = "".join([str(c) for c in sorted(qfp)])

        sf_perms = elim_perms(
            sorted(qfp),
            2,
            [
                (1, 4),
                (1, 5),
                (8, 4),
                (8, 5),
                (2, 3),
                (2, 6),
                (7, 3),
                (7, 6),
                (4, 1),
                (4, 8),
                (5, 1),
                (5, 8),
            ],
        )
        for sfp in sf_perms:
            sfs = "".join([str(c) for c in sorted(sfp)])

            f_perms = elim_perms(sorted(sfp), 1, [])

            for fp in f_perms:
                fs = "".join([str(c) for c in fp])
                bracket_str = f"{qfs}_{sfs}_{fs}"
                counts[bracket_str] = []

    async with tpa_cm() as tpa:
        skipped_lt_8 = []
        skipped_bad_data = []

        for bar, year in tqdm_bar(range(2010, 2021)):
            for event in [
                e
                async for e in tpa.get_events_by_year(year=year)
                if e.event_type in EventType.STANDARD_EVENT_TYPES
            ]:
                bar.set_description(event.key)
                a = [a async for a in tpa.get_event_alliances(event_key=event.key)]
                if len(a) != 8:
                    skipped_lt_8.append(event.key)
                    continue

                s = elim_str(
                    [a async for a in tpa.get_event_alliances(event_key=event.key)],
                    event.key,
                )
                if s not in counts:
                    skipped_bad_data.append(event.key)
                    continue

                counts[s].append(event.key)

    with file_cm(get_savepath("out.tsv"), "w+") as f:
        for bracket, events in sorted(counts.items(), key=lambda t: -len(t[1])):
            f.write(f"{bracket}\t{len(events)}\t{', '.join(events)}\n")

    print(f"{skipped_bad_data=}")
    print(f"{skipped_lt_8=}")

    n_counts = defaultdict(lambda: 0)
    for bracket, events in counts.items():
        n_counts[bracket[-1]] += len(events)

    print(n_counts)


@expose
async def test(key):
    async with tpa_cm() as tpa:
        print([ea async for ea in tpa.get_event_alliances(event_key=key)])
