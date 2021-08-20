from py.cli import expose
from pprint import pprint
from py.multiproc.mp import call, sum_, FnArgs


@expose
def testz():
    pprint(
        call(
            sum_,
            [[FnArgs(args=[1, 2, i])] for i in range(10)],
        )
    )
