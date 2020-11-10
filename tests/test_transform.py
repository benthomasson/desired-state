
from ansible_state.transform import transform_state
from .util import load_state, load_rule



def test_transform_state():
    a = load_state('reorder_list', 'A')
    b = load_state('reorder_list', 'B')
    rules = load_rule('routers_with_id')
    assert a != b
    assert transform_state(a, rules) == transform_state(b, rules)
