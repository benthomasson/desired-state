

"""
Usage:
    ansible-state [options] init <state.yml> <playbook.yml>
    ansible-state [options] watch [--init] <state.yml> <playbook.yml>

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


class PlaybookRunner:

    def __init__(self, new_desired_state, state_diff, playbook, secrets, project_src, inventory):
        print('PlaybookRunner')
        self.inventory = inventory
        self.secrets = secrets
        self.project_src = project_src
        self.new_desired_state = new_desired_state
        self.state_diff = convert_diff(state_diff)
        self.playbook = playbook
        self.runner_thread = None
        self.shutdown_requested = False
        self.shutdown = False

        self.build_project_directory()
        self.copy_files()
        self.write_settings()
        self.write_cmdline()
        self.write_passwords()
        self.write_state_vars()
        self.write_diff_vars()
        self.write_playbook()
        self.write_inventory()
        self.start_ansible_playbook()

    def build_project_directory(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ansible_state_playbook")
        print(self.temp_dir)
        ensure_directory(os.path.join(self.temp_dir, 'env'))
        ensure_directory(os.path.join(self.temp_dir, 'project'))
        ensure_directory(os.path.join(self.temp_dir, 'project', 'roles'))

    def copy_files(self):
        src = os.path.abspath(self.project_src)
        dest = os.path.join(self.temp_dir, 'project')
        src_files = os.listdir(src)
        for file_name in src_files:
            full_file_name = os.path.join(src, file_name)
            if (os.path.isfile(full_file_name)):
                shutil.copy(full_file_name, dest)
            if (os.path.isdir(full_file_name)):
                shutil.copytree(full_file_name, os.path.join(dest, file_name))

    def write_settings(self):
        with open(os.path.join(self.temp_dir, 'env', 'settings'), 'w') as f:
            f.write(json.dumps(dict(idle_timeout=0,
                                    job_timeout=0)))

    def write_cmdline(self):
        with open(os.path.join(self.temp_dir, 'env', 'cmdline'), 'w') as f:
            f.write("--ask-become-pass -v")

    def write_passwords(self):
        with open(os.path.join(self.temp_dir, 'env', 'passwords'), 'w') as f:
            f.write("""---\n"SUDO password:": "{0}"\nBECOME password: "{0}"\n...""".format(self.secrets['become']))

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

    def write_diff_vars(self):
        diff_vars_file = os.path.join(self.temp_dir, 'project', 'diff_vars.yml')
        with open(diff_vars_file, 'w') as f:
            f.write(yaml.safe_dump(self.state_diff, default_flow_style=False))
        for play in self.playbook:
            play['tasks'].insert(0, {'include_vars': {'file': 'diff_vars.yml', 'name': 'diff'}})

    def write_inventory(self):
        print("inventory set to %s", self.inventory)
        with open(os.path.join(self.temp_dir, 'inventory'), 'w') as f:
            f.write(self.inventory)

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
        print(self.temp_dir)

    def cancel_callback(self):
        print('cancel_callback called')
        return self.shutdown_requested

    def finished_callback(self, runner):
        print('finished_callback called')
        self.shutdown = True

    def runner_process_message(self, data):
        # print("runner message:\n{}".format(pprint.pformat(data)))
        print(data.get('stdout', ''))


class DiffHandler:

    def __init__(self, state_path, playbook_path, queue, secrets, project_src, inventory):
        self.inventory = inventory
        self.queue = queue
        self.state_path = state_path
        self.playbook_path = playbook_path
        self.secrets = secrets
        self.project_src = project_src
        with open(self.state_path) as f:
            self.current_desired_state = yaml.safe_load(f.read())
        with open(self.playbook_path) as f:
            self.original_playbook = yaml.safe_load(f.read())
        pprint.pprint(self.current_desired_state)

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
        with open(self.playbook_path) as f:
            current_playbook = yaml.safe_load(f.read())
        print(self.current_desired_state)
        print(new_desired_state)
        state_diff = dict(DeepDiff(self.current_desired_state, new_desired_state))
        playbook_diff = dict(DeepDiff(self.original_playbook, new_playbook))
        if len(state_diff):
            print('state_diff', state_diff)
        if len(playbook_diff):
            print('playbook_diff', playbook_diff)
        if len(state_diff) or len(playbook_diff):
            # v0 execute ansible to resolve the desired state by running a playbook
            self.original_playbook = new_playbook
            PlaybookRunner(new_desired_state,
                           state_diff,
                           current_playbook,
                           self.secrets,
                           self.project_src,
                           self.inventory)
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

    if parsed_args['init']:
        return ansible_state_init(parsed_args)
    elif parsed_args['watch']:
        return ansible_state_watch(parsed_args)
    else:
        assert False, 'Update the docopt'


def inventory(parsed_args):

    if not parsed_args['--inventory']:
        return  "[all]\nlocalhost ansible_connection=local\n"

    with open(parsed_args['--inventory']) as f:
        return f.read()


def ansible_state_init(parsed_args, secrets=None):

    secrets = secrets or defaultdict(str)

    if parsed_args['--ask-become-pass'] and not secrets['become']:
        secrets['become'] = getpass()

    with open(os.path.abspath(os.path.expanduser(parsed_args['<state.yml>']))) as f:
        state = yaml.safe_load(f.read())

    with open(os.path.abspath(os.path.expanduser(parsed_args['<playbook.yml>']))) as f:
        playbook = yaml.safe_load(f.read())

    project_src = os.path.abspath(os.path.expanduser(parsed_args['--project-src']))

    PlaybookRunner(state, {}, playbook, secrets, project_src, inventory(parsed_args))


def ansible_state_watch(parsed_args):

    secrets = defaultdict(str)

    if parsed_args['--ask-become-pass']:
        secrets['become'] = getpass()

    if parsed_args['--init']:
        ansible_state_init(parsed_args, secrets)

    project_src = os.path.abspath(os.path.expanduser(parsed_args['--project-src']))

    threads = []

    queue = Queue()

    diff_handler = DiffHandler(os.path.abspath(os.path.expanduser(parsed_args['<state.yml>'])),
                               os.path.abspath(os.path.expanduser(parsed_args['<playbook.yml>'])),
                               queue,
                               secrets,
                               project_src,
                               inventory(parsed_args))

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
