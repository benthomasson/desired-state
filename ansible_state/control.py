

import gevent
import yaml
from gevent.queue import Queue
from gevent_fsm.fsm import FSMController, Channel

from . import control_fsm

from .messages import Control, DesiredState, now
from .monitor import AnsibleStateMonitor
from .collection import load_rules, load_schema, split_collection_name
from .validate import validate


class AnsibleStateControl(object):

    '''
    A control is a green thread FSM that controls multiple monitors (monitor.py) in one or more
    systems.   Each system is managed by one or more monitors and is defined by a set of desired
    state configurations.  A set of desired state configurations that work together defines a system.
    For instance a set of linux, networking, and application desired state configurations would
    define a system in this terminology.  The control would bring up the linux, networking, and
    application configurations in the correct order to bring the system from zero to a completely
    working application.
    '''

    def __init__(self, sequence, tracer, fsm_id, control_id, secrets, stream, control_plane):
        self.sequence = sequence
        self.service_instances = dict()
        self.workers = dict()
        self.control_id = control_id
        self.secrets = secrets
        self.tracer = tracer
        self.stream = stream
        self.control_plane = control_plane
        self.buffered_messages = Queue()
        self.controller = FSMController(
            self, "control_fsm", fsm_id, control_fsm.Start, self.tracer, self.tracer)
        self.controller.outboxes['default'] = Channel(
            self.controller, self.controller, self.tracer, self.buffered_messages)
        self.queue = self.controller.inboxes['default']
        self.control_plane.put_message(Control(next(sequence), now(), self.control_id))
        self.thread = gevent.spawn(self.controller.receive_messages)

    def start_monitor(self, service_instance):
        # Get schema
        schema = load_schema(
            *split_collection_name(service_instance.schema_name))
        print(schema)
        # Get rules
        rules = load_rules(*split_collection_name(service_instance.rules_name))
        print(rules)
        # Get inventory
        inventory = service_instance.inventory
        print(inventory)
        validate(yaml.safe_load(service_instance.config), schema)
        project_src = '.'
        worker = AnsibleStateMonitor(self.tracer,
                                     0,
                                     self.secrets,
                                     project_src,
                                     rules,
                                     yaml.safe_load(service_instance.config),
                                     inventory,
                                     self.stream)
        self.workers[service_instance.id] = worker

        self.service_instances[service_instance.id] = service_instance

    def update_monitor(self, service_instance):
        schema = load_schema(
            *split_collection_name(service_instance.schema_name))
        validate(yaml.safe_load(service_instance.config), schema)
        self.workers[service_instance.id].queue.put(
            DesiredState(0, 0, service_instance.config))

    def start_or_update_monitor(self, service_instance):
        if service_instance.id in self.workers:
            self.update_monitor(service_instance)
        else:
            self.start_monitor(service_instance)
