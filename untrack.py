#! /usr/bin/env python3
# -*- coding:utf-8 -*-

"""untrack

A tool to rm large file of git.

Usage:
  untrack list [-n=<lf-number>]
  untrack rm <path-pattern> [-f]
  untrack reset
  untrack confirm

Options:
  list               list large file order by size desc.

  rm                 remove large file according to pattern.
                     and then you can use command `confirm` to confirm the rm
                     or  command `reset` to undo the rm.

  reset              reset the rm status.
  confirm            update the branch to confirm the rm.

  <path-pattern>     such as ./target/*.zip.

  -n=<lf-number>     large file number to show [default: 10].
  -f --force-remove  WARNING: rm and confirm, no undo!

"""

from sh import git
from sh import sort
from sh import tail
from sh import awk
from sh import grep
from sh import ErrorReturnCode_1
from color import color
from docopt import docopt

from glob import glob

__version__ = '0.0.1'


def max_file_hash(n=10):
    pack_path = glob('.git/objects/pack/*.idx')

    if not pack_path:
        git.gc()
        pack_path = glob('.git/objects/pack/*.idx')

    try:
        return awk(tail(sort(git('verify-pack',
                             '-v',
                             pack_path), '-k', '3', '-n'), '-{0:d}'.format(n)), '{print $1}')
    except ErrorReturnCode_1 as ex:
        color.print_err(ex)
        return None


def max_file_hash_name(n=10):
    """name may be empty"""
    hash_result = max_file_hash(n)

    if hash_result is None:
        return None

    details_result = []
    for line in hash_result:
        try:
            details_result.append(grep(git('rev-list', '--objects', '--all'), '-i', line.strip()))
        except ErrorReturnCode_1:
            details_result.append(None)

    return details_result


def remove_from_history(path, confirm=False):
    cmd = [
        'filter-branch',
        '-f',
        '--prune-empty',
        '--index-filter',
        'git rm -rf --cached --ignore-unmatch {0}'.format(path),
        '--tag-name-filter',
        'cat',
        '--',
        '--all'
    ]

    run_cmd = git(cmd)

    if confirm:
        confirm_remove()

    return run_cmd


def confirm_remove():
    git(git('for-each-ref', '--format=delete %(refname)', 'refs/original'), 'update-ref', '--stdin')
    git.reflog('expire', '--expire=now', '--all')
    git.gc('--prune=now')


def reset():
    try:
        git.reset('--hard', 'refs/original/refs/heads/master')
    except ErrorReturnCode_1 as ex:
        print(ex)

def cli():
    arguments = docopt(__doc__, version=__version__)

    if arguments['list']:
        n = arguments['-n']
        color.print_info(max_file_hash_name(n))


if __name__ == '__main__':
    cli()