import inspect
from pprint import pformat

from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer

fns = dict()


def expose(fn):
    fname = fn.__name__
    module = inspect.getmodule(fn)
    module_name = module.__name__.split(".")[-1]

    if module_name not in fns:
        fns[module_name] = dict()

    fns[module_name][fname] = fn


def attempt_to_cast_value(s):
    try:
        return int(s)
    except ValueError:
        pass

    try:
        return float(s)
    except ValueError:
        pass

    return s


def run_main(argv):
    module_name, fn_name, *args = argv
    args = [attempt_to_cast_value(a) for a in args]
    fns[module_name][fn_name](*args)


def pprint(*args, **kwargs):
    print(highlight(pformat(*args, **kwargs), PythonLexer(), Terminal256Formatter()))
