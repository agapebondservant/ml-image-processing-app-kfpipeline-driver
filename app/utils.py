import logging
from collections import defaultdict
import sys
import os
import re


def get_cmd_arg(name):
    d = defaultdict(list)
    for cmd_args in sys.argv[1:]:
        cmd_arg = cmd_args.split('=')
        if len(cmd_arg) == 2:
            d[cmd_arg[0].lstrip('-')].append(cmd_arg[1].replace('"', ''))

    if name in d:
        return str(d[name][0])
    else:
        logging.info('Unknown command line arg requested: {}'.format(name))


def get_env_var(name):
    if name in os.environ:
        value = os.environ[name]
        return int(value) if re.match("\d+$", value) else value
    else:
        logging.info('Unknown environment variable requested: {}'.format(name))
