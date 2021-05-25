from pathlib import Path


def create_dir_if_not_exists(name: str):
    Path(name).mkdir(parents=True, exist_ok=True)


def team_key_to_num(s: str) -> int:
    s = s[3:]
    if s[-1].isnumeric():
        return int(s)
    else:
        return int(s[:-1])


