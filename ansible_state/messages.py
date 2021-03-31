
from collections import namedtuple
import yaml
import json


def serialize(message):
    return [message.__class__.__name__.encode(), yaml.dump(dict(message._asdict())).encode()]

def json_serialize(message):
    return json.dumps([message.__class__.__name__, dict(message._asdict())]).encode()

def json_deserialize(message):
    data = json.loads(message)
    if isinstance(data, list):
        msg_type = data[0]
        msg_data = data[1]
        if msg_type in msg_types:
            try:
                return msg_types[msg_type](**msg_data)
            except BaseException as e:
                print(e)
                raise
    return None


Hello = namedtuple('Hello', [])
FSMState = namedtuple('FSMState', ['state'])
Diff = namedtuple('Diff', ['diff'])
ValidationResult = namedtuple('ValidationResult', ['host', 'result'])
ValidationTask = namedtuple('ValidationTask', ['host', 'task_action', 'result'])

DesiredState = namedtuple('DesiredState', ['id', 'client_id', 'desired_state'])
ActualState = namedtuple('ActualState', ['id', 'client_id', 'actual_state'])
Poll = namedtuple('Poll', [])
Complete = namedtuple('Complete', [])
Difference = namedtuple('Difference', [])
NoDifference = namedtuple('NoDifference', [])
Success = namedtuple('Success', [])
Failure = namedtuple('Failure', [])

Inventory = namedtuple('Inventory', ['inventory'])
Rules = namedtuple('Rules', ['rules'])

Control = namedtuple('Control', ['id'])
System = namedtuple('System', ['id', 'control_id'])
Monitor = namedtuple('Monitor', ['id', 'system_id', 'control_id'])

DesiredSystemState = namedtuple('DesiredSystemState', ['id', 'client_id', 'desired_state'])

Shutdown = namedtuple('Shutdown', [])

ServiceInstance = namedtuple('ServiceInstance', ['id',
                                                 'service_id',
                                                 'created_at',
                                                 'deleted_at',
                                                 'name',
                                                 'config',
                                                 'inventory',
                                                 'inventory_id',
                                                 'collection',
                                                 'service_name',
                                                 'schema_name',
                                                 'rules_name'])

msg_types = {x.__name__: x for x in [DesiredState, ActualState, Hello, Control, ServiceInstance]}
