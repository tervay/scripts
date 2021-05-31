from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Tuple, TypeVar, Union, List

from tqdm import tqdm
from tqdm.asyncio import tqdm as atqdm

from protos.tpa import (
    Event,
    MatchScoreBreakdown2015,
    MatchScoreBreakdown2016,
    MatchScoreBreakdown2017,
    MatchScoreBreakdown2018,
    MatchScoreBreakdown2019,
    MatchScoreBreakdown2020,
    Schedule,
)
from py.tba import EventType
from py.tpa.context_manager import tpa_cm
import datetime

save_dir = "out"

MatchScoreBreakdown = Union[
    MatchScoreBreakdown2015,
    MatchScoreBreakdown2016,
    MatchScoreBreakdown2017,
    MatchScoreBreakdown2018,
    MatchScoreBreakdown2019,
    MatchScoreBreakdown2020,
]

T = TypeVar("T")

OPPOSITE_COLOR = {"blue": "red", "red": "blue"}

MAX_TEAMS_PAGE_NUM = 17


def create_dir_if_not_exists(name: str):
    Path(name).mkdir(parents=True, exist_ok=True)


def team_key_to_num(s: str) -> int:
    s = s[3:]
    if s[-1].isnumeric():
        return int(s)
    else:
        return int(s[:-1])


@contextmanager
def file_cm(path, mode):
    create_dir_if_not_exists("/".join(path.split("/")[:-1]))
    f = open(path, mode)
    try:
        yield f
    finally:
        f.close()


def get_savepath(fname):
    return f"{save_dir}/{fname}"


async def get_real_event_schedule(event_key: str):
    async with tpa_cm() as tpa:
        teams = [t async for t in tpa.get_event_teams(event_key=event_key)]
        matches = [
            m
            async for m in tpa.get_event_matches(event_key=event_key)
            if m.comp_level == "qm"
        ]
        matches.sort(key=lambda m: m.match_number)

        unseen_keys = set([t.key for t in teams])
        for m in matches:
            for a in [m.alliances.blue, m.alliances.red]:
                for k in a.team_keys:
                    if k in unseen_keys:
                        unseen_keys.remove(k)

        tk_to_team = {t.key: t for t in teams}
        for k in unseen_keys:
            teams.remove(tk_to_team[k])

        return Schedule(teams=teams, matches=matches)


def is_official_event(event: Event) -> bool:
    return event.event_type in EventType.SEASON_EVENT_TYPES


def clamp(num, min_value, max_value):
    return max(min(num, max_value), min_value)


def tqdm_bar(iterable: Iterable[T]) -> Tuple[tqdm, T]:
    bar = tqdm(iterable)
    for item in bar:
        yield (bar, item)


async def tqdm_bar_async(iterable: Iterable[T]) -> Tuple[atqdm, T]:
    bar = atqdm(iterable)
    for item in bar:
        yield (bar, item)


def flatten_lists(lists):
    return [item for sublist in lists for item in sublist]


async def flatten_lists_async(lists):
    return [item for sublist in lists async for item in sublist]


async def flatten_lists_aiter(lists):
    for l in lists:
        async for item in l:
            yield item


def sort_events(events: List[Event]) -> List[Event]:
    return sorted(
        events, key=lambda e: datetime.datetime.strptime(e.end_date, "%Y-%m-%d")
    )


def filter_completed_events(event_list: List[Event]) -> List[Event]:
    return list(filter(is_completed_event, event_list))


def is_completed_event(event: Event) -> bool:
    return (
        datetime.datetime.strptime(event.end_date, "%Y-%m-%d") < datetime.datetime.now()
    )


def filter_official_events(events: List[Event]):
    return list(filter(is_official_event, events))


def is_official_event(event: Event) -> bool:
    return event.event_type in EventType.SEASON_EVENT_TYPES
