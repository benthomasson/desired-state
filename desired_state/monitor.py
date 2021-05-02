

import gevent
import yaml
from gevent.queue import Queue
from gevent_fsm.fsm import FSMController, Channel

from . import reconciliation_fsm

from .messages import Inventory, Rules, DesiredState, now


def convert_inventory(inventory):
    '''
        Converts an inventory from a YAML string to a data structure.
    '''
    inventory = yaml.safe_load(inventory)
    return inventory


class DesiredStateMonitor(object):

    '''
    A monitor is a green thread FSM that monitors the lifecycle of one
    desired state configuration defined by one schema.   The FSM is defined by
    the reconciliation_fsm.py file.  The monitor receives state changes from
    its `queue` and sends status messages out of its `stream`.
    '''

    def __init__(self, tracer, fsm_id, secrets, project_src, rules, current_desired_state, inventory, stream):
        self.secrets = secrets
        self.project_src = project_src
        self.rules = rules
        self.ran_rules = []
        self.new_desired_state = None
        self.current_desired_state = current_desired_state
        self.discovered_actual_state = None
        self.operational_actual_state = None
        self.inventory = inventory
        self.tracer = tracer
        self.stream = stream
        self.buffered_messages = Queue()
        self.controller = FSMController(
            self, "reconciliation_fsm", fsm_id, reconciliation_fsm.Start, self.tracer, self.tracer)
        self.controller.outboxes['default'] = Channel(
            self.controller, self.controller, self.tracer, self.buffered_messages)
        self.queue = self.controller.inboxes['default']
        self.stream.put_message(Inventory(0, now(), convert_inventory(inventory)))
        self.stream.put_message(Rules(0, now(), rules))
        self.stream.put_message(DesiredState(0, now(), 0, 0, current_desired_state))
        self.thread = gevent.spawn(self.controller.receive_messages)
