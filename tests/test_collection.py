

from desired_state.collection import find_collection


def test_find_collection():
    location = find_collection('benthomasson.expect')
    assert location is not None



