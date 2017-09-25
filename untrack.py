#! /usr/bin/env python3
# -*- coding:utf-8 -*-

"""untrack

A tool to rm large file of git.

Usage:
  untrack list [-n=<lf-number>]
  untrack rm <path-pattern>... [-f]
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
  -f                 WARNING: rm and confirm, no undo!

"""

from sh import git
from sh import sort
from sh import tail
from sh import awk
from sh import grep
from sh import ErrorReturnCode_1
from sh import ErrorReturnCode_128
from color import color
from docopt import docopt

from glob import glob
import re
import os

__version__ = '0.0.1'


class RebundantResetException(Exception):
    def __str__(self):
        return 'Don\'t need to reset'


def in_git_repo():
    try:
        git.status()
    except ErrorReturnCode_128:
        return False
    else:
        return True


def in_toplevel_of_repo():
    if in_git_repo() and os.path.isdir('.git'):
        return True
    else:
        return False


def max_file_hash(n=10, short=False):
    pack_path = glob('.git/objects/pack/*.idx')

    if not pack_path:
        git.gc()
        pack_path = glob('.git/objects/pack/*.idx')

    if short:
        return awk(tail(sort(git('verify-pack', '-v', pack_path), '-k', '3'),
                        '-n',
                        '-{0:d}'.format(n)),
                   '{print $1}')
    else:
        return tail(sort(git('verify-pack', '-v', pack_path), '-k', '3', '-n'),
                    '-{0:d}'.format(n))


def format_num(num, split_len=3, split_char=',',):
    """
    Example:
        format_num(1000000000000000,split_char='_',split_len=3)
        '1_000_000_000_000_000'
    :param num:
    :param split_len:
    :param split_char:
    :return:formatted str
    """
    assert split_len > 0

    l = [c + split_char if i % split_len == 0 else c for i, c in enumerate(reversed(str(num)))]
    snum = ''.join(l[::-1])[:-1]

    return snum


def max_file_hash_name(n=10):
    """name may be empty"""

    hash_result = max_file_hash(n)
    if hash_result is None:
        return None

    details_result = []
    for line in hash_result:
        if not re.match('[a-f0-9]{40}\W+[a-z]+\W+\d+\W+\d+\W+\d+', line):
            continue

        line_list = re.split('\W+', line)

        hash_fn = grep(git('rev-list', '--objects', '--all'), '-i', line_list[0]).__str__().strip()
        match_item = '{0} {1} KB'.format(hash_fn, format_num(int(line_list[2])))
        details_result.append(match_item)

    return details_result


def remove_from_history(paths, confirm=False):
    cmd = [
        'filter-branch',
        '-f',
        '--prune-empty',
        '--index-filter',
        'git rm -rf --cached --ignore-unmatch {0}'.format(' '.join(paths)),
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

    except ErrorReturnCode_128 as ex:
        raise RebundantResetException from ex


def cli():
    arguments = docopt(__doc__, version=__version__)

    if not in_toplevel_of_repo():
        color.print_err('Not in toplevel of a git repo.')
        return

    if arguments['list']:
        n = int(arguments['-n'])

        result = max_file_hash_name(n)
        if result is not None:
            [color.print_info(item) for item in result]

    elif arguments['rm']:
        path_pattern = arguments['<path-pattern>']
        force = True if arguments['-f'] else False

        result = remove_from_history(path_pattern, force)
        color.print_ok(result)
        color.print_warn('run `untrack confirm` to confirm the op')

    elif arguments['reset']:
        try:
            reset()
        except ErrorReturnCode_1 as ex:
            color.print_err(ex)
        except RebundantResetException as ex:
            color.print_warn(ex)
        else:
            color.print_ok('reset.')

    elif arguments['confirm']:
        confirm_remove()
        color.print_ok('confirm remove.')


if __name__ == '__main__':
    cli()