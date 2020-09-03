

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
from watchdog.observers import Observer

logger = logging.getLogger('cli')


class PrintHandler:

    def dispatch(self, event):
        print(event)


event_handler = PrintHandler()


def watch_files(path):
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
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

    threads.append(gevent.spawn(watch_files, os.path.dirname(os.path.abspath(parsed_args['<state.yml>']))))

    print(threads)

    try:
        gevent.joinall(threads)
    except KeyboardInterrupt:
        print('Caught KeyboardInterrupt')
    print('Completed')
    return 0
