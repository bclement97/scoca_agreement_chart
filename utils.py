from __future__ import print_function
import os.path
import sys


_parent_dir = os.path.dirname(os.path.realpath(__file__))


def absolute_path(*rel_paths):
    return os.path.join(_parent_dir, *rel_paths)


def print_err(*msg):
    print('ERROR:', *msg, file=sys.stderr)