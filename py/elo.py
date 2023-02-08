from collections import defaultdict
import json
from typing import List
from py.tpa import tpa_cm
from py.cli import expose

from py.util import all_events_with_bar, is_official_event

import trueskill as ts


@expose
async def generate():
    elos = defaultdict(dict)
    curr_ratings = {}
    active = defaultdict(lambda: False)

    def rating(team_key: str) -> ts.Rating:
        if team_key not in curr_ratings:
            curr_ratings[team_key] = ts.Rating()

        return curr_ratings[team_key]

    def update_ratings(
        ratings: List[ts.Rating], red: List[str], blue: List[str]
    ) -> None:
        new_red, new_blue = ratings
        for nr, r in zip(new_red, red):
            curr_ratings[r] = nr
        for nb, b in zip(new_blue, blue):
            curr_ratings[b] = nb

    async with tpa_cm() as tpa:
        prev_year = None
        async for event in all_events_with_bar(
            tpa,
            year_start=2009,
            year_end=2022,
            condition=is_official_event,
        ):
            if prev_year is not None and event.year != prev_year:
                for k in curr_ratings.keys():
                    if active[k]:
                        elos[k[3:]][prev_year] = curr_ratings[k].mu
                        # v.pi *= (1 / (1.25 ** 2))

                    curr_ratings[k] = ts.Rating(
                        mu=curr_ratings[k].mu,
                        sigma=(curr_ratings[k].sigma + ts.Rating().sigma) / 2,
                    )

                active = defaultdict(lambda: False)

            async for match in tpa.get_event_matches(event_key=event.key):
                red = [x for x in match.alliances.red.team_keys]
                blue = [x for x in match.alliances.blue.team_keys]
                red_ratings = [rating(x) for x in red]
                blue_ratings = [rating(x) for x in blue]

                for k in red + blue:
                    active[k] = True

                ranks = (
                    [
                        0 if match.winning_alliance in ["red", ""] else 1,
                        0 if match.winning_alliance in ["blue", ""] else 1,
                    ]
                    if event.year != 2015
                    else [
                        0
                        if match.alliances.red.score >= match.alliances.blue.score
                        else 1,
                        0
                        if match.alliances.blue.score >= match.alliances.red.score
                        else 1,
                    ]
                )

                new_ratings = ts.rate([red_ratings, blue_ratings], ranks=ranks)

                update_ratings(new_ratings, red, blue)

            prev_year = event.year

        for k, v in curr_ratings.items():
            if active[k]:
                elos[k[3:]][prev_year] = v.mu

        with open("py/data/elos.json", "w+") as f:
            json.dump(elos, fp=f, indent=4)
