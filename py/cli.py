import inspect

from py.tpa.context_manager import close

fns = dict()


def expose(fn):
    fname = fn.__name__
    module = inspect.getmodule(fn)
    module_name = module.__name__.split(".")[-1]

    if module_name not in fns:
        fns[module_name] = dict()

    fns[module_name][fname] = fn
    return fn


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

    if s.lower() in ["none", "null"]:
        return None

    return s


async def run_main(argv):
    module_name, fn_name, *args = argv
    args = [attempt_to_cast_value(a) for a in args]
    fn = fns[module_name][fn_name]

    if inspect.iscoroutinefunction(fn):
        await fn(*args)
        close()
    else:
        fn(*args)
