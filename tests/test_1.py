

from deepdiff import DeepDiff

def test_1():
    t1 = {1:1, 2:2, 3:3}
    t2 = t1
    assert DeepDiff(t1, t2) == {}
