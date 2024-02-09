import logging
import timeit

import requests
from tbapy import TBA

logging.basicConfig(level=logging.DEBUG)


def perf_tbapy():
    tba = TBA("1EhUOwczJi4vDUXza94fAo7s4UFrKgBrTJ6A3MTeYR0WrgzlyGR0Tzyl1TN2P6Tu")
    t = timeit.timeit(lambda: tba.teams(year=2023), number=1)

    print(f"tbapy took {t}")


def perf_requests():
    session = requests.Session()

    t = timeit.timeit(
        lambda: [
            session.get(
                url=f"https://www.thebluealliance.com/api/v3/teams/{i}",
                headers={
                    "X-TBA-Auth-Key": "1EhUOwczJi4vDUXza94fAo7s4UFrKgBrTJ6A3MTeYR0WrgzlyGR0Tzyl1TN2P6Tu"
                },
            ).json()
            for i in range(1, 18)
        ],
        number=1,
    )
    print(f"Requests took {t}")


if __name__ == "__main__":
    perf_tbapy()
    perf_requests()
