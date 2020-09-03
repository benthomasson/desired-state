

"""
Usage:
    ansible-state [options] run <state.yml>

Options:
    -h, --help       Show this page
    --debug          Show debug logging
    --verbose        Show verbose logging
"""

from gevent import monkey
monkey.patch_all()
import logging
FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='ansible_state.log', level=logging.DEBUG, format=FORMAT)  # noqa
logging.debug('Logging started')
logging.debug('Loading runner')
import ansible_runner
logging.debug('Loaded runner')
from deepdiff import DeepDiff
from watchdog.events import FileCreatedEvent, FileModifiedEvent
from watchdog_gevent import Observer
import pprint
import tempfile
import yaml
import sys
import os
import json
from gevent.queue import Queue
from docopt import docopt
import gevent

FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='ansible_fsm.log', level=logging.DEBUG, format=FORMAT)  # noqa


logger = logging.getLogger('cli')


def ensure_directory(d):
    if not os.path.exists(d):
        os.mkdir(d)


class PlaybookRunner:

    def __init__(self):
        print('PlaybookRunner')
        self.default_inventory = "[all]\nlocalhost ansible_connection=local\n"
        self.default_play = yaml.dump(dict(hosts='localhost',
                                           name='default',
                                           gather_facts=False))
        self.runner_thread = None
        self.shutdown_requested = False
        self.shutdown = False
        self.temp_dir = tempfile.mkdtemp(prefix="ansible_state_playbook")
        print(self.temp_dir)
        ensure_directory(os.path.join(self.temp_dir, 'env'))
        ensure_directory(os.path.join(self.temp_dir, 'project'))
        ensure_directory(os.path.join(self.temp_dir, 'project', 'roles'))
        with open(os.path.join(self.temp_dir, 'env', 'settings'), 'w') as f:
            f.write(json.dumps(dict(idle_timeout=0,
                                    job_timeout=0)))
        self.playbook_file = (os.path.join(self.temp_dir, 'project', 'playbook.yml'))
        playbook = []
        current_play = yaml.load(self.default_play, Loader=yaml.FullLoader)
        playbook.append(current_play)
        with open(self.playbook_file, 'w') as f:
            f.write(yaml.safe_dump(playbook, default_flow_style=False))
        self.write_inventory(self.default_inventory)
        self.start_ansible_playbook()

    def write_inventory(self, inventory):
        print("inventory set to %s", inventory)
        with open(os.path.join(self.temp_dir, 'inventory'), 'w') as f:
            f.write("\n".join(inventory.splitlines()[1:]))

    def start_ansible_playbook(self):
        print('start_ansible_playbook')
        #self.runner_thread = gevent.spawn(ansible_runner.run,
        #                                  private_data_dir=self.temp_dir,
        #                                  playbook="playbook.yml",
        #                                  quiet=True,
        #                                  debug=True,
        #                                  ignore_logging=True,
        #                                  cancel_callback=self.cancel_callback,
        #                                  finished_callback=self.finished_callback,
        #                                  event_handler=self.runner_process_message)
        ansible_runner.run(private_data_dir=self.temp_dir,
                           playbook="playbook.yml",
                           quiet=True,
                           debug=True,
                           ignore_logging=True,
                           cancel_callback=self.cancel_callback,
                           finished_callback=self.finished_callback,
                           event_handler=self.runner_process_message)
        print('spawned ansible runner')

    def cancel_callback(self):
        print('cancel_callback called')
        return self.shutdown_requested

    def finished_callback(self, runner):
        print('finished_callback called')
        self.shutdown = True

    def runner_process_message(self, data):
        print("runner message:\n{}".format(pprint.pformat(data)))


class DiffHandler:

    def __init__(self, path, queue):
        self.queue = queue
        self.path = os.path.abspath(os.path.expanduser(path))
        self.dir_path = os.path.dirname(self.path)
        with open(self.path) as f:
            self.current_state = yaml.safe_load(f.read())
        pprint.pprint(self.current_state)

    def recieve_messages(self):
        print('recieve_messages')
        while True:
            self.dispatch(self.queue.get())

    def dispatch(self, event):
        if isinstance(event, FileCreatedEvent) and event.src_path == self.path:
            print('created')
            self.diff()
        if isinstance(event, FileModifiedEvent) and event.src_path == self.path:
            print('modified')
            self.diff()

    def diff(self):
        print('diff')
        with open(self.path) as f:
            new_state = yaml.safe_load(f.read())
        print(self.current_state)
        print(new_state)
        print(DeepDiff(self.current_state, new_state))
        if DeepDiff(self.current_state, new_state):
            PlaybookRunner()
            self.current_state = new_state


class FileWatcher:

    def __init__(self, queue):
        self.queue = queue

    def dispatch(self, event):
        self.queue.put(event)


def watch_files(path, queue):
    print('watch_files')
    event_handler = FileWatcher(queue)
    observer = Observer()
    dir_path = os.path.dirname(os.path.abspath(path))
    print(dir_path)
    observer.schedule(event_handler, dir_path, recursive=True)
    print('observer.start')
    observer.start()
    print('observer.join')
    observer.join()
    print('observer.done')


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

    queue = Queue()

    diff_handler = DiffHandler(os.path.abspath(os.path.expanduser(parsed_args['<state.yml>'])), queue)

    threads.append(gevent.spawn(watch_files, os.path.abspath(os.path.expanduser(parsed_args['<state.yml>'])), queue))
    threads.append(gevent.spawn(diff_handler.recieve_messages))

    print(threads)

    try:
        gevent.joinall(threads)
    except KeyboardInterrupt:
        print('Caught KeyboardInterrupt')
    print('Completed')
    return 0
