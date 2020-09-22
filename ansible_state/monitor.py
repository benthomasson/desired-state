

import gevent
from gevent.queue import Queue
from gevent_fsm.fsm import FSMController, Channel

from . import resolution_fsm


class AnsibleStateMonitor(object):

    def __init__(self, tracer, fsm_id, secrets, project_src, rules, current_desired_state, inventory):
        self.secrets = secrets
        self.project_src = project_src
        self.rules = rules
        self.current_desired_state = current_desired_state
        self.inventory = inventory
        self.tracer = tracer
        self.buffered_messages = Queue()
        self.controller = FSMController(self, "resolution_fsm", fsm_id, resolution_fsm.Start, self.tracer, self.tracer)
        self.controller.outboxes['default'] = Channel(self.controller, self.controller, self.tracer, self.buffered_messages)
        self.queue = self.controller.inboxes['default']
        self.thread = gevent.spawn(self.controller.receive_messages)
