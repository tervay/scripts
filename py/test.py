from pprint import pprint

from py.cli import expose
from py.multiproc.mp import FnArgs, call, sum_


@expose
def testz():
    pprint(
        call(
            sum_,
            [[FnArgs(args=[1, 2, i])] for i in range(10)],
        )
    )
