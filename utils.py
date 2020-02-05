from __future__ import print_function

import os.path


_parent_dir = os.path.dirname(os.path.realpath(__file__))


def project_path(*rel_paths):
    return os.path.join(_parent_dir, *rel_paths)


def log(msg, *f):
    # TODO: log
    print(msg.format(*f))


def warn(msg, *f):
    log('WARNING: ' + msg, *f)


def error(err, msg, *f):
    log('ERROR: ' + msg, *f)
    raise err
