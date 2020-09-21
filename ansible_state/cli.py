

"""
Usage:
    ansible-state [options] monitor <current-state.yml> <rules.yml>
    ansible-state [options] update-desired-state <new-state.yml>
    ansible-state [options] update-system-state <new-state.yml>

Options:
    -h, --help              Show this page
    --debug                 Show debug logging
    --verbose               Show verbose logging
    --explain               Do not run the rules, only print the ones that would run.
    --ask-become-pass       Ask for the become password
    --project-src=<d>       Copy project files this directory [default: .]
    --inventory=<i>         Inventory to use
    --cwd=<c>               Change working directory on start
"""

from gevent import monkey
monkey.patch_all()
import gevent
import logging
import sys
import os
import yaml
from docopt import docopt

from .monitor import AnsibleStateMonitor
from .client import ZMQClientChannel
from .server import ZMQServerChannel
from .util import ConsoleTraceLog
from .messages import DesiredState, SystemState

FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='ansible_state.log', level=logging.DEBUG, format=FORMAT)  # noqa
logging.debug('Logging started')
logging.debug('Loading runner')
logging.debug('Loaded runner')

FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='ansible_fsm.log', level=logging.DEBUG, format=FORMAT)  # noqa

logger = logging.getLogger('cli')


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

    if parsed_args['--cwd']:
        os.chdir(parsed_args['--cwd'])

    if parsed_args['monitor']:
        return ansible_state_monitor(parsed_args)
    elif parsed_args['update-desired-state']:
        return ansible_state_update_desired_state(parsed_args)
    elif parsed_args['update-system-state']:
        return ansible_state_update_system_state(parsed_args)
    else:
        assert False, 'Update the docopt'


def inventory(parsed_args):

    if not parsed_args['--inventory']:
        return "[all]\nlocalhost ansible_connection=local\n"

    with open(parsed_args['--inventory']) as f:
        return f.read()


def ansible_state_monitor(parsed_args):

    tracer = ConsoleTraceLog()
    worker = AnsibleStateMonitor(tracer, 0)
    server = ZMQServerChannel(worker.queue, tracer)
    worker.controller.outboxes['output'] = server.queue
    gevent.joinall([worker.thread, server.zmq_thread, server.controller_thread])
    return 0


def check_state(state):

    yaml.safe_load(state)


def ansible_state_update_desired_state(parsed_args):

    with open(parsed_args['<new-state.yml>']) as f:
        new_state = f.read()
        check_state(new_state)

    client = ZMQClientChannel()
    client.send(DesiredState(0, 0, new_state))
    return 0


def ansible_state_update_system_state(parsed_args):

    with open(parsed_args['<new-state.yml>']) as f:
        new_state = f.read()
        check_state(new_state)

    client = ZMQClientChannel()
    client.send(SystemState(0, 0, new_state))
    return 0
