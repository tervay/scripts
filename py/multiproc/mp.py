import multiprocessing as mp
from time import sleep
from typing import Callable, Dict, List, NamedTuple

from py.util import flatten_lists
from tqdm import tqdm


class FnArgs(NamedTuple):
    args: List = []
    kwargs: Dict = {}


def call_individual(f: Callable, arg_list: List[FnArgs]):
    results = []
    for args in arg_list:
        results.append(f(*args.args, **args.kwargs))

    return results


def call(f: Callable, args: List[List[FnArgs]], flatten: bool = True):
    pool = mp.Pool(processes=len(args))

    results = pool.starmap(
        call_individual,
        tqdm([(f, x) for x in args], total=len(args)),
    )

    pool.close()
    return results if not flatten else flatten_lists(results)


def sum_(*vals):
    sleep(max(vals))
    return sum(vals)
