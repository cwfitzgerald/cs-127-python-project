import os


def relative_path(base, extant):
    return os.path.join(os.path.dirname(os.path.realpath(base)), extant)


def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper
