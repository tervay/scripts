from typing import Dict, List, Literal, Tuple

import requests
from requests_cache import CachedSession
from protos.tpa import Event, Team
from py.cli import pprint

LongLat = Tuple[float, float]

Service = Literal["route", "nearest", "table", "match", "trip", "tile"]
Format = Literal["json", "flatbuffers"]
Profile = Literal["car", "bike", "foot"]

base_url = "https://router.project-osrm.org"
session = CachedSession(cache_name="requests_cache")


def get(
    service: Service,
    coordinates: List[LongLat],
    profile: Profile = "car",
    format: Format = "json",
    version: str = "v1",
    extra_args: Dict[str, str] = {},
):
    coord_str = ";".join([f"{c[0]},{c[1]}" for c in coordinates])
    kwarg_str = "&".join([f"{k}={v}" for k, v in extra_args.items()])
    url = f"{base_url}/{service}/{version}/{profile}/{coord_str}?{kwarg_str}"
    return session.get(url=url).json()


def matrix(
    coordinates: List[LongLat], labels: List[str], extra_args: Dict[str, str] = {}
) -> Dict[str, Dict[str, float]]:
    data = get(service="table", coordinates=coordinates, extra_args=extra_args)
    pprint(data)

    ret = {}
    for i, l1 in enumerate(labels):
        if l1 not in ret:
            ret[l1] = {}

        for j, l2 in enumerate(labels):
            if l1 == l2:
                continue

            if l2 not in ret[l1]:
                ret[l1][l2] = {}

            ret[l1][l2] = data["durations"][i][j]

    return ret


def event_matrix(event: Event, teams: List[Team]) -> Dict[str, float]:
    data = get(
        service="table",
        coordinates=[(event.lng, event.lat)] + [(t.lng, t.lat) for t in teams],
        extra_args={"destinations": "0"},
    )

    if "durations" not in data:
        for t in teams:
            if (t.lng, t.lat) == (0.0, 0.0):
                print(t)

        print("")
        print(event.key)
        pprint(data)
        exit(0)

    return {team.key: data["durations"][i][0] for i, team in enumerate(teams, start=1)}
