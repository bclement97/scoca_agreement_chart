from __future__ import print_function

import os.path
import sys


_parent_dir = os.path.dirname(os.path.realpath(__file__))


def project_path(*rel_paths):
    return os.path.join(_parent_dir, *rel_paths)


def log(msg, file=sys.stdout):
    # TODO: log
    if file is not None:
        print(msg, file=file)


def warn(msg):
    msg = 'WARNING: ' + msg
    log(msg)


def error(msg):
    msg = 'ERROR: ' + msg
    log(msg, file=sys.stderr)
