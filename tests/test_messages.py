

from ansible_state.messages import json_serialize, json_deserialize, Hello, Control

def test_hello():
    s = json_serialize(Hello())
    o = json_deserialize(s)
    assert o == Hello()


def test_control():
    s = json_serialize(Control(5))
    o = json_deserialize(s)
    assert o == Control(5)
