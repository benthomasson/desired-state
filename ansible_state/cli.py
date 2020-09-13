

"""
Usage:
    ansible-state [options] diff <old-state.yml> <new-state2.yml> <rules.yml>

Options:
    -h, --help              Show this page
    --debug                 Show debug logging
    --verbose               Show verbose logging
    --ask-become-pass       Ask for the become password
    --project-src=<d>       Copy project files this directory [default: .]
    --inventory=<i>         Inventory to use
"""

from gevent import monkey
monkey.patch_all()
import logging
import ansible_runner
from deepdiff import DeepDiff
from watchdog.events import FileCreatedEvent, FileModifiedEvent
from watchdog_gevent import Observer
import pprint
import tempfile
import yaml
import sys
import os
import json
from collections import defaultdict
from getpass import getpass
from gevent.queue import Queue
from docopt import docopt
import gevent
import shutil
FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='ansible_state.log', level=logging.DEBUG, format=FORMAT)  # noqa
logging.debug('Logging started')
logging.debug('Loading runner')
logging.debug('Loaded runner')

FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='ansible_fsm.log', level=logging.DEBUG, format=FORMAT)  # noqa


logger = logging.getLogger('cli')


def ensure_directory(d):
    if not os.path.exists(d):
        os.mkdir(d)


def convert_diff(diff):

    if 'dictionary_item_added' in diff:
        diff['dictionary_item_added'] = [str(x) for x in diff['dictionary_item_added']]
    return diff

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = docopt(__doc__, args)
    if parsed_args['--debug']:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed_args['--verbose']:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    if parsed_args['diff']:
        return ansible_state_diff(parsed_args)
    else:
        assert False, 'Update the docopt'


def inventory(parsed_args):

    if not parsed_args['--inventory']:
        return  "[all]\nlocalhost ansible_connection=local\n"

    with open(parsed_args['--inventory']) as f:
        return f.read()


def ansible_state_diff(parsed_args):


    return 0
