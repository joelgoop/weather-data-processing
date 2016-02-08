from contextlib import contextmanager
from collections import defaultdict
from itertools import tee, izip
import os
import codecs

@contextmanager
def addpath(path):
    """
    Context manager to add a path to PATH temporarily.

    Args:
        path (str): path to add
    """
    orig_path = os.environ['PATH']
    os.environ['PATH'] = path+';'+os.environ['PATH']
    yield
    os.environ['PATH'] = orig_path


def quote_identifier(s, errors="strict"):
    """
    Escape and quote string for use as identifier in SQLite.

    Args:
        s: string to quote
        errors: error handling in codecs
    """
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return "\"" + encodable.replace("\"", "\"\"") + "\""

# Multi-level dictionary defaulting to itself. Adds new levels automatically.
multilevel_dict = lambda: defaultdict(multilevel_dict)

def pairwise(iterable):
    """
    Iterate pairwise over some sequence.
    s -> (s0,s1), (s1,s2), (s2, s3), ...

    Args:
        iterable: iterable to create pairs from

    Returns:
        iterator<tuple>: new iterator containing pairs
    """
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
