import gzip
import json
import os
import pathlib
import re

from py.tba import models

cache_dir = "cache"
fn_dir = "fn"
api_dir = "api"

pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)


# https://github.com/django/django/blob/master/django/utils/text.py#L219
def get_valid_filename(s):
    s = str(s).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", s)


def call(fn, refresh=False, *args, **kwargs):
    filepath = (
        f"{cache_dir}{fn_dir}{get_valid_filename(fn.__name__)}_{get_valid_filename(str(args))}_"
        f"{get_valid_filename(kwargs)}"
    )
    pathlib.Path(filepath).mkdir(parents=True, exist_ok=True)

    if os.path.exists(f"{filepath}.json.gz") and not refresh:
        with gzip.open(f"{filepath}.json.gz", "rb") as f:
            content = json.loads(f.read())

        return content
    else:
        data = fn(*args, **kwargs)
        with gzip.open(f"{filepath}.json.gz", "wb+") as f:
            f.write(json.dumps(data).encode())

        if isinstance(data, models._base_model_class):
            data = dict(data)

        return data


def url_to_filepath(url):
    return f"{cache_dir}/{get_valid_filename(url)}"


def write_to_cache(url, data):
    with gzip.open(f"{url_to_filepath(url)}.json.gz", "wb+") as f:
        f.write(json.dumps(data).encode())


def read_from_cache(url):
    try:
        with gzip.open(f"{url_to_filepath(url)}.json.gz", "rb") as f:
            content = json.loads(f.read())

        return content
    except FileNotFoundError:
        return None
