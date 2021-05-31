import inspect
from pprint import pformat

from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer

from py.tpa.context_manager import close, tpa_cm

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

    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False

    return s


async def run_main(argv):
    module_name, fn_name, *args = argv
    args = [attempt_to_cast_value(a) for a in args]
    fn = fns[module_name][fn_name]

    if inspect.iscoroutinefunction(fn):
        await ((fn(*args)))
        close()
    else:
        fn(*args)


def pprint(*args, **kwargs):
    print(highlight(pformat(*args, **kwargs), PythonLexer(), Terminal256Formatter()))
