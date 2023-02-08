import datetime
from contextlib import contextmanager
from io import TextIOWrapper
from math import sqrt
from pathlib import Path
from typing import (
    AsyncIterator,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import bar_chart_race as bcr
import pandas as pd
from async_lru import alru_cache
from rich import get_console
from rich.bar import Bar
from rich.table import Table
from tqdm.asyncio import tqdm as atqdm
from tqdm.rich import tqdm

from protos.tpa import (
    Event,
    Match,
    MatchScoreBreakdown2015,
    MatchScoreBreakdown2016,
    MatchScoreBreakdown2017,
    MatchScoreBreakdown2018,
    MatchScoreBreakdown2019,
    MatchScoreBreakdown2020,
    Schedule,
    Team,
    TpaStub,
)
from py.tba import EventType
from py.tpa.context_manager import tpa_cm

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
ENABLE_GEOCODING = False

MAX_TEAMS_PAGE_NUM = 17
MAX_TEAMS_PAGE_RANGE = 17 + 1
CURRENT_YEAR = datetime.datetime.today().year
CURRENT_YEAR_RANGE = CURRENT_YEAR + 1

STATE_TO_SHORT = {
    "Alabama": "AL",
    "Alaska": "AK",
    "American Samoa": "AS",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Guam": "GU",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Northern Mariana Islands": "MP",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Puerto Rico": "PR",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virgin Islands": "VI",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    # Canada
    "Newfoundland": "NL",
    "Prince Edward Island": "PE",
    "Nova Scotia": "NS",
    "New Brunswick": "NB",
    "Quebec": "QC",
    "Québec": "QC",
    "Ontario": "ON",
    "Manitoba": "MB",
    "Alberta": "AB",
    "British Columbia": "BC",
    "Yukon": "YT",
    "Yukon Territory": "YT",
    "Northwest Territories": "NT",
    "Nunavut": "NU",
    "Saskatchewan": "SK",
}
SHORT_TO_STATE = dict(map(reversed, STATE_TO_SHORT.items()))


def create_dir_if_not_exists(name: str):
    Path(name).mkdir(parents=True, exist_ok=True)


def team_key_to_num(s: str) -> int:
    s = s[3:]
    if s[-1].isnumeric():
        return int(s)
    else:
        return int(s[:-1])


@contextmanager
def file_cm(path, mode) -> TextIOWrapper:
    create_dir_if_not_exists("/".join(path.split("/")[:-1]))
    f = open(path, mode)
    try:
        yield f
    finally:
        f.close()


def get_savepath(fname):
    return f"{save_dir}/{fname}"


@alru_cache(maxsize=250)
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


def tqdm_bar(iterable: List[T]) -> Generator[Tuple[tqdm, T], None, None]:
    bar = tqdm(iterable)
    for item in bar:
        item = item  # type: T # type-hint hack since tqdm doesn't have type support
        yield (bar, item)


async def tqdm_bar_async(
    iterable: Iterable[T],
) -> Generator[Tuple[atqdm, T], None, None]:
    bar = atqdm(iterable)
    for item in bar:
        yield (bar, item)


def flatten_lists(lists: List[List[T]]) -> List[T]:
    return [item for sublist in lists for item in sublist]


async def flatten_lists_async(lists: List[List[T]]) -> List[T]:
    return [item for sublist in lists async for item in sublist]


async def flatten_lists_aiter(lists):
    for l in lists:
        async for item in l:
            yield item


def sort_events(events: List[Event]) -> List[Event]:
    return sorted(
        events, key=lambda e: datetime.datetime.strptime(e.end_date, "%Y-%m-%d")
    )


def sort_matches(matches: List[Match]) -> List[Match]:
    match_type_order = ["qm", "ef", "qf", "sf", "f"]
    return sorted(
        matches,
        key=lambda m: (
            match_type_order.index(m.comp_level),
            m.set_number,
            m.match_number,
        ),
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


def chunkify(a, n):
    k, m = divmod(len(a), n)
    return list(a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))


def make_table(col_names: List[str], row_vals: List[List[any]]) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    for col in col_names:
        table.add_column(col)

    for row in row_vals:
        table.add_row(*[str(r) for r in row])

    return table


def make_table_from_dict(
    d: Dict[str, any],
    sort_by=lambda r: r[1],
    reverse=True,
    round_to: Optional[int] = None,
    max_width: Optional[int] = None,
    col_names: List[str] = ["K", "V"],
) -> Table:
    if max_width is None:
        max_width = round(get_console().width * 0.5)

    keys = [k for k in d.keys()]
    rows = []
    for k in keys:
        row = [k]
        if type(d[k]) is list:
            row.extend([v if round_to is None else round(v, round_to) for v in d[k]])
        else:
            row.append(d[k] if round_to is None else round(d[k], round_to))
        rows.append(row)

    rows.sort(key=sort_by, reverse=reverse)
    max_value = round(max([sort_by(rows[0]), sort_by(rows[-1])]))

    for row in rows:
        row.append(
            "".join(
                [
                    [c for c in s.__rich_repr__()][0]
                    for s in Bar(
                        size=(sort_by(row) * max_width / max_value),
                        begin=0,
                        end=max_width,
                        width=round(sort_by(row) * max_width / max_value),
                    ).__rich_console__(
                        console=get_console(), options=get_console().options
                    )
                    if s.text != "\n"
                ]
            )
        )

    return make_table(col_names=col_names, row_vals=rows)


def find(a: Iterable[T], cond: Callable[[T], bool]) -> Optional[T]:
    for i in a:
        if cond(i):
            return i

    return None


def _confidence(ups, downs, z=1.96):
    n = ups + downs

    if n == 0:
        return 0

    phat = float(ups) / n
    return (
        phat + z * z / (2 * n) - z * sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    ) / (1 + z * z / n)


def wilson_sort(
    objs: List[T],
    positive: Callable[[T], float],
    negative: Callable[[T], float],
    minimum_total: float = 0,
    z: float = 1.96,
) -> List[T]:
    return [
        i
        for i in sorted(objs, key=lambda e: -_confidence(positive(e), negative(e), z=z))
        if (positive(i) + negative(i)) >= minimum_total
    ]


async def all_events_with_bar(
    tpa: TpaStub,
    year_start: int,
    year_end: int,
    condition: Callable[[Event], bool],
    limit: Optional[int] = None,
) -> AsyncIterator[Event]:
    events = []  # type: List[Event]
    try:
        for year in range(year_start, year_end + 1):
            async for event in tpa.get_events_by_year(year=year):
                if condition(event) and (limit is None or len(events) < limit):
                    events.append(event)
                    if len(events) == limit:
                        raise StopIteration()
    except (StopIteration, StopAsyncIteration):
        pass

    for bar, event in tqdm_bar(events):
        bar.set_description(event.key.rjust(10))
        yield event


class Leaderboard(list):
    def __init__(
        self,
        fn: Callable = lambda t: t,
        highest_first: bool = True,
        limit: Optional[int] = None,
    ) -> None:
        self.fn = fn
        self.highest_first = highest_first
        self.limit = limit

    def append(self, __object) -> None:
        super().append(__object)
        self.sort(reverse=self.highest_first, key=self.fn)
        if self.limit is not None:
            while len(self) > self.limit:
                del self[-1]


class BarChartRaceHelper:
    def __init__(self) -> None:
        self.all_teams = [str(n) for n in range(1, 10000)]
        self.df = pd.DataFrame(columns=self.all_teams, dtype="int32")

    def update(self, counts: Dict[str, int], date: str):
        self.df = self.df.append(
            pd.DataFrame(
                [[int(counts[t]) for t in self.all_teams]],
                columns=self.all_teams,
                dtype="int32",
                index=[date],
            )
        )

    def make(self, filename: str, title: str, bars: int, period_length: int = 500):
        self.df = self.df.loc[:, (self.df != 0).any(axis=0)]
        bcr.bar_chart_race(
            df=self.df,
            filename=f"out/{filename}",
            n_bars=bars,
            title=title,
            period_length=period_length,
            steps_per_period=int(round(60 / 1000 * period_length)),
        )


def event_is_official(event: Event):
    return event.event_type in EventType.STANDARD_EVENT_TYPES
