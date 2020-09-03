

"""
Usage:
    ansible-state [options] run <state.yml>

Options:
    -h, --help       Show this page
    --debug          Show debug logging
    --verbose        Show verbose logging
"""

from gevent import monkey
monkey.patch_all(thread=False)
import gevent

import logging
FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='ansible_fsm.log', level=logging.DEBUG, format=FORMAT)  # noqa

from docopt import docopt
import logging
import os
import sys
import yaml
from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent, FileModifiedEvent
from deepdiff import DeepDiff

logger = logging.getLogger('cli')


class DiffHandler:

    def __init__(self, path):
        self.path = os.path.abspath(os.path.expanduser(path))
        self.dir_path = os.path.dirname(self.path)
        with open(self.path) as f:
            self.current_state = yaml.safe_load(f.read())

    def dispatch(self, event):
        print(event)
        print(type(event))
        print(event.src_path)
        if isinstance(event, FileCreatedEvent) and event.src_path == self.path:
            print('created')
            self.diff()
        if isinstance(event, FileModifiedEvent) and event.src_path == self.path:
            print('modified')
            self.diff()

    def diff(self):
        with open(self.path) as f:
            new_state = yaml.safe_load(f.read())
        print(self.current_state)
        print(new_state)
        print(DeepDiff(self.current_state, new_state))


def watch_files(path):
    event_handler = DiffHandler(path)
    observer = Observer()
    dir_path = os.path.dirname(os.path.abspath(path))
    observer.schedule(event_handler, dir_path, recursive=True)
    observer.start()
    observer.join()


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

    if parsed_args['run']:
        return ansible_state_run(parsed_args)
    else:
        assert False, 'Update the docopt'


def ansible_state_run(parsed_args):

    threads = []

    threads.append(gevent.spawn(watch_files, os.path.abspath(os.path.expanduser(parsed_args['<state.yml>']))))

    print(threads)

    try:
        gevent.joinall(threads)
    except KeyboardInterrupt:
        print('Caught KeyboardInterrupt')
    print('Completed')
    return 0
