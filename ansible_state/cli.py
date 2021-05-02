

"""
Usage:
    desired-state [options] control [<control-id>]
    desired-state [options] monitor <current-state.yml> [<rules.yml>]
    desired-state [options] from <initial-state.yml> to <new-state.yml> [<rules.yml>]
    desired-state [options] update-desired-state <new-state.yml>
    desired-state [options] update-actual-state <new-state.yml>
    desired-state [options] validate <state.yml> <schema.yml>

Options:
    -h, --help              Show this page
    --debug                 Show debug logging
    --verbose               Show verbose logging
    --explain               Do not run the rules, only print the ones that would run.
    --ask-become-pass       Ask for the become password
    --project-src=<d>       Copy project files this directory [default: .]
    --inventory=<i>         Inventory to use
    --cwd=<c>               Change working directory on start
    --stream=<s>            Websocket channel to stream telemetry to
    --control-plane=<s>     Websocket channel to connect to the control plane
"""

from .stream import WebsocketChannel, NullChannel
from .messages import DesiredState, ActualState, Shutdown, now
from .util import ConsoleTraceLog, check_state
from .server import ZMQServerChannel
from .client import ZMQClientChannel
from .monitor import DesiredStateMonitor
from .control import DesiredStateControl
from .validate import get_errors, validate
from .collection import split_collection_name, has_rules, has_schema, load_rules, load_schema
from .types import get_meta
import gevent_fsm.conf
import gevent.exceptions
from getpass import getpass
from collections import defaultdict
from docopt import docopt
import yaml
import os
import sys
import logging
from uuid import uuid4
import gevent
from gevent import monkey
monkey.patch_all()


FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
logging.basicConfig(filename='/tmp/desired_state.log', level=logging.DEBUG, format=FORMAT)  # noqa
logging.debug('Logging started')
logging.debug('Loading runner')
logging.debug('Loaded runner')

logger = logging.getLogger('cli')


def main(args=None):
    '''
    Main function for the CLI.
    '''

    if args is None:
        args = sys.argv[1:]
    parsed_args = docopt(__doc__, args)
    if parsed_args['--debug']:
        logging.basicConfig(level=logging.DEBUG)
        gevent_fsm.conf.settings.instrumented = True
    elif parsed_args['--verbose']:
        gevent_fsm.conf.settings.instrumented = True
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    if parsed_args['--cwd']:
        os.chdir(parsed_args['--cwd'])

    if parsed_args['control']:
        return desired_state_control(parsed_args)
    elif parsed_args['monitor']:
        return desired_state_monitor(parsed_args)
    elif parsed_args['from'] and parsed_args['to']:
        return desired_state_from_to(parsed_args)
    elif parsed_args['update-desired-state']:
        return desired_state_update_desired_state(parsed_args)
    elif parsed_args['update-actual-state']:
        return desired_state_update_actual_state(parsed_args)
    elif parsed_args['validate']:
        return desired_state_validate(parsed_args)
    else:
        assert False, 'Update the docopt'


def inventory(parsed_args, state):
    '''
    Loads an inventory
    '''

    meta = get_meta(state)

    if meta.inventory and os.path.exists(meta.inventory):
        print('inventory:', meta.inventory)
        with open(meta.inventory) as f:
            return f.read()
    elif not parsed_args['--inventory']:
        print('inventory:', 'localhost only')
        return "all:\n  hosts:\n    localhost: ansible_connection=local\n"
    else:
        print('inventory:', parsed_args['--inventory'])
        with open(parsed_args['--inventory']) as f:
            return f.read()


def validate_state(state):
    '''
    Validates state using schema if it is found in the meta data of the state.
    '''

    meta = get_meta(state)

    if meta.schema:
        if os.path.exists(meta.schema):
            with open(meta.schema) as f:
                schema = yaml.safe_load(f.read())
        elif has_schema(*split_collection_name(meta.schema)):
            schema = load_schema(*split_collection_name(meta.schema))
        else:
            schema = {}
        validate(state, schema)


def parse_options(parsed_args):

    secrets = defaultdict(str)

    if parsed_args['--ask-become-pass'] and not secrets['become']:
        secrets['become'] = getpass()

    if parsed_args['--stream']:
        stream = WebsocketChannel(parsed_args['--stream'])
    else:
        stream = NullChannel()

    project_src = os.path.abspath(
        os.path.expanduser(parsed_args['--project-src']))

    return secrets, project_src, stream


def load_rules_from_args_or_meta(parsed_args, state):

    meta = get_meta(state)

    if parsed_args['<rules.yml>']:
        if os.path.exists(parsed_args['<rules.yml>']):
            with open(parsed_args['<rules.yml>']) as f:
                rules = yaml.safe_load(f.read())
        elif has_rules(*split_collection_name(parsed_args['<rules.yml>'])):
            rules = load_rules(
                *split_collection_name(parsed_args['<rules.yml>']))
        else:
            raise Exception('No rules file found')
    elif meta.rules:
        if os.path.exists(meta.rules):
            with open(meta.rules) as f:
                rules = yaml.safe_load(f.read())
        elif has_rules(*split_collection_name(meta.rules)):
            rules = load_rules(*split_collection_name(meta.rules))
        else:
            raise Exception('No rules file found')
    else:
        raise Exception('No rules file found')

    return rules


def desired_state_control(parsed_args):
    secrets, _, stream = parse_options(parsed_args)
    control_id = parsed_args['<control-id>'] or str(uuid4())

    if parsed_args['--control-plane']:
        control_plane = WebsocketChannel(parsed_args['--control-plane'])
    else:
        control_plane = NullChannel()

    threads = []

    if stream.thread:
        threads.append(stream.thread)

    tracer = ConsoleTraceLog()
    control = DesiredStateControl(
        tracer, 0, control_id, secrets, stream, control_plane)
    control_plane.outbox = control.queue
    threads.append(control.thread)

    server = ZMQServerChannel(control.queue, tracer)
    threads.append(server.zmq_thread)
    threads.append(server.controller_thread)
    control.controller.outboxes['output'] = server.queue
    gevent.joinall(threads)


def desired_state_monitor(parsed_args):
    '''
    Starts the state monitoring green thread.
    '''

    secrets, project_src, stream = parse_options(parsed_args)

    threads = []

    if stream.thread:
        threads.append(stream.thread)

    with open(parsed_args['<current-state.yml>']) as f:
        current_desired_state = yaml.safe_load(f.read())

    validate_state(current_desired_state)

    rules = load_rules_from_args_or_meta(parsed_args, current_desired_state)

    tracer = ConsoleTraceLog()
    worker = DesiredStateMonitor(tracer, 0, secrets, project_src, rules, current_desired_state, inventory(
        parsed_args, current_desired_state), stream)
    threads.append(worker.thread)
    server = ZMQServerChannel(worker.queue, tracer)
    threads.append(server.zmq_thread)
    threads.append(server.controller_thread)
    worker.controller.outboxes['output'] = server.queue
    gevent.joinall(threads)
    return 0


def desired_state_from_to(parsed_args):
    '''
    Calculates the differene in state from initial-state to new-state executes those changes and exits.
    '''

    secrets, project_src, stream = parse_options(parsed_args)

    threads = []

    if stream.thread:
        threads.append(stream.thread)

    with open(parsed_args['<initial-state.yml>']) as f:
        initial_desired_state = yaml.safe_load(f.read())

    validate_state(initial_desired_state)

    with open(parsed_args['<new-state.yml>']) as f:
        new_desired_state = f.read()

    validate_state(yaml.safe_load(new_desired_state))

    rules = load_rules_from_args_or_meta(parsed_args, initial_desired_state)

    tracer = ConsoleTraceLog()
    worker = DesiredStateMonitor(tracer, 0, secrets, project_src, rules, initial_desired_state, inventory(
        parsed_args, initial_desired_state), stream)
    threads.append(worker.thread)
    worker.queue.put(DesiredState(0, now(), 0, 0, new_desired_state))
    worker.queue.put(Shutdown())
    gevent.joinall([worker.thread])
    return 0


def desired_state_update_desired_state(parsed_args):
    '''
    Sends a new desired state to the monitor green thread.
    '''

    with open(parsed_args['<new-state.yml>']) as f:
        new_state = f.read()
        check_state(new_state)

    validate_state(yaml.safe_load(new_state))

    client = ZMQClientChannel()
    client.send(DesiredState(0, now(), 0, 0, new_state))
    return 0


def desired_state_update_actual_state(parsed_args):
    '''
    Sends a new actual state to the monitor green thread.
    '''

    with open(parsed_args['<new-state.yml>']) as f:
        new_state = f.read()
        check_state(new_state)

    validate_state(yaml.safe_load(new_state))

    client = ZMQClientChannel()
    client.send(ActualState(0, 0, new_state))
    return 0


def desired_state_validate(parsed_args):
    '''
    Validates a state using the schema and prints a list of errors in the state.
    '''

    with open(parsed_args['<state.yml>']) as f:
        state = yaml.safe_load(f.read())

    with open(parsed_args['<schema.yml>']) as f:
        schema = yaml.safe_load(f.read())

    for error in get_errors(state, schema):
        print(error)
    else:
        return 0
    return 1



if __name__ == "__main__":
    main()

