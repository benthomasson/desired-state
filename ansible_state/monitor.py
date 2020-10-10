

import gevent
import yaml
import json
from gevent.queue import Queue
from gevent_fsm.fsm import FSMController, Channel

from . import resolution_fsm

from .messages import Inventory, Rules, DesiredState


def convert_inventory(inventory):
    inventory = yaml.safe_load(inventory)
    return inventory



class AnsibleStateMonitor(object):

    def __init__(self, tracer, fsm_id, secrets, project_src, rules, current_desired_state, inventory, stream):
        self.secrets = secrets
        self.project_src = project_src
        self.rules = rules
        self.ran_rules = []
        self.new_desired_state = None
        self.current_desired_state = current_desired_state
        self.discovered_system_state = None
        self.operational_system_state = None
        self.inventory = inventory
        self.tracer = tracer
        self.stream = stream
        self.buffered_messages = Queue()
        self.controller = FSMController(self, "resolution_fsm", fsm_id, resolution_fsm.Start, self.tracer, self.tracer)
        self.controller.outboxes['default'] = Channel(self.controller, self.controller, self.tracer, self.buffered_messages)
        self.queue = self.controller.inboxes['default']
        self.stream.put_message(Inventory(convert_inventory(inventory)))
        self.stream.put_message(Rules(rules))
        self.stream.put_message(DesiredState(0, 0, current_desired_state))
        self.thread = gevent.spawn(self.controller.receive_messages)
