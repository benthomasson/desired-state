
from collections import namedtuple
import yaml


def serialize(message):
    return [message.__class__.__name__.encode(), yaml.dump(dict(message._asdict())).encode()]


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

DesiredState = namedtuple('DesiredState', ['id', 'client_id', 'desired_state'])

Shutdown = namedtuple('Shutdown', [])

msg_types = {x.__name__: x for x in [DesiredState, ActualState]}
