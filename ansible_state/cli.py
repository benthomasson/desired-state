

"""
Usage:
    ansible-state [options] run <state.yml> <playbook.yml>

Options:
    -h, --help       Show this page
    --debug          Show debug logging
    --verbose        Show verbose logging
"""

from gevent import monkey
monkey.patch_all()
import gevent
from docopt import docopt
from gevent.queue import Queue
import json
import os
import sys
import yaml
import tempfile
import pprint
from watchdog_gevent import Observer
from watchdog.events import FileCreatedEvent, FileModifiedEvent
from deepdiff import DeepDiff
import ansible_runner
import logging
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


class PlaybookRunner:

    def __init__(self, new_desired_state, state_diff, playbook):
        print('PlaybookRunner')
        self.new_desired_state = new_desired_state
        self.state_diff = state_diff
        self.inventory = "[all]\nlocalhost ansible_connection=local\n"
        self.playbook = playbook
        self.runner_thread = None
        self.shutdown_requested = False
        self.shutdown = False

        self.build_project_directory()
        self.write_settings()
        self.write_state_vars()
        self.write_playbook()
        self.write_inventory()
        self.start_ansible_playbook()

    def build_project_directory(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ansible_state_playbook")
        print(self.temp_dir)
        ensure_directory(os.path.join(self.temp_dir, 'env'))
        ensure_directory(os.path.join(self.temp_dir, 'project'))
        ensure_directory(os.path.join(self.temp_dir, 'project', 'roles'))

    def write_settings(self):
        with open(os.path.join(self.temp_dir, 'env', 'settings'), 'w') as f:
            f.write(json.dumps(dict(idle_timeout=0,
                                    job_timeout=0)))

    def write_playbook(self):
        self.playbook_file = (os.path.join(self.temp_dir, 'project', 'playbook.yml'))
        playbook = self.playbook
        with open(self.playbook_file, 'w') as f:
            f.write(yaml.safe_dump(playbook, default_flow_style=False))

    def write_state_vars(self):
        state_vars_file = os.path.join(self.temp_dir, 'project', 'state_vars.yml')
        with open(state_vars_file, 'w') as f:
            f.write(yaml.safe_dump(self.new_desired_state, default_flow_style=False))
        for play in self.playbook:
            play['tasks'].insert(0, {'include_vars': {'file': 'state_vars.yml', 'name': 'state'}})

    def write_inventory(self):
        print("inventory set to %s", self.inventory)
        with open(os.path.join(self.temp_dir, 'inventory'), 'w') as f:
            f.write("\n".join(self.inventory.splitlines()[1:]))

    def start_ansible_playbook(self):
        print('start_ansible_playbook')
        # self.runner_thread = gevent.spawn(ansible_runner.run,
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

    def __init__(self, state_path, playbook_path, queue):
        self.queue = queue
        self.state_path = state_path
        self.playbook_path = playbook_path
        with open(self.state_path) as f:
            self.current_desired_state = yaml.safe_load(f.read())
        with open(self.playbook_path) as f:
            self.original_playbook = yaml.safe_load(f.read())
        with open(self.playbook_path) as f:
            self.current_playbook = yaml.safe_load(f.read())
        pprint.pprint(self.current_desired_state)
        pprint.pprint(self.current_playbook)

    def recieve_messages(self):
        print('recieve_messages')
        while True:
            self.dispatch(self.queue.get())

    def dispatch(self, event):
        if isinstance(event, FileCreatedEvent) and event.src_path == self.state_path:
            print('created')
            self.diff()
        elif isinstance(event, FileModifiedEvent) and event.src_path == self.state_path:
            print('modified')
            self.diff()
        if isinstance(event, FileCreatedEvent) and event.src_path == self.playbook_path:
            print('created')
            self.diff()
        elif isinstance(event, FileModifiedEvent) and event.src_path == self.playbook_path:
            print('modified')
            self.diff()

    def diff(self):
        print('diff')
        with open(self.state_path) as f:
            new_desired_state = yaml.safe_load(f.read())
        with open(self.playbook_path) as f:
            new_playbook = yaml.safe_load(f.read())
        print(self.current_desired_state)
        print(new_desired_state)
        state_diff = dict(DeepDiff(self.current_desired_state, new_desired_state))
        playbook_diff = dict(DeepDiff(self.original_playbook, new_playbook))
        if len(state_diff):
            print('state_diff')
        if len(playbook_diff):
            print('playbook_diff')
        if len(state_diff) or len(playbook_diff):
            # v0 execute ansible to resolve the desired state by running a playbook
            self.original_playbook = new_playbook
            PlaybookRunner(new_desired_state, state_diff, self.current_playbook)
            # v0 assume that the state was set correctly
            self.current_desired_state = new_desired_state


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

    diff_handler = DiffHandler(os.path.abspath(os.path.expanduser(parsed_args['<state.yml>'])),
                               os.path.abspath(os.path.expanduser(parsed_args['<playbook.yml>'])),
                               queue)

    threads.append(gevent.spawn(watch_files, os.path.abspath(os.path.expanduser(parsed_args['<state.yml>'])), queue))
    threads.append(gevent.spawn(watch_files, os.path.abspath(os.path.expanduser(parsed_args['<playbook.yml>'])), queue))
    threads.append(gevent.spawn(diff_handler.recieve_messages))

    print(threads)

    try:
        gevent.joinall(threads)
    except KeyboardInterrupt:
        print('Caught KeyboardInterrupt')
    print('Completed')
    return 0
