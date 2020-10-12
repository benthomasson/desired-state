
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
SystemState = namedtuple('SystemState', ['id', 'client_id', 'system_state'])
Poll = namedtuple('Poll', [])
Complete = namedtuple('Complete', [])
Difference = namedtuple('Difference', [])
NoDifference = namedtuple('NoDifference', [])
Success = namedtuple('Success', [])
Failure = namedtuple('Failure', [])

Inventory = namedtuple('Inventory', ['inventory'])
Rules = namedtuple('Rules', ['rules'])


# Task = namedtuple('Task', ['id', 'client_id', 'task'])
# Inventory = namedtuple('Inventory', ['id', 'inventory'])
# Cancel = namedtuple('Cancel', ['id', 'client_id'])
# TaskComplete = namedtuple('TaskComplete', ['id', 'client_id'])
# PlaybookFinished = namedtuple('PlaybookFinished', ['id', 'client_id'])
# Error = namedtuple('Error', ['id', 'client_id'])
# RunnerStdout = namedtuple('RunnerStdout', ['id', 'client_id', 'data'])
# RunnerMessage = namedtuple('RunnerMessage', ['id', 'client_id', 'data'])
# RunnerCancelled = namedtuple('RunnerCancelled', ['id', 'client_id'])
# ShutdownComplete = namedtuple('ShutdownComplete', ['id', 'client_id'])
# ShutdownRequested = namedtuple('ShutdownRequested', [])

# StatusMessage = namedtuple('StatusMessage', ['message'])
# TaskCompletionMessage = namedtuple('TaskCompletionMessage', ['task_num'])

msg_types = {x.__name__: x for x in [DesiredState, SystemState]}
