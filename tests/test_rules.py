
from deepdiff import DeepDiff, extract

import re

import yaml

from ansible_state.util import make_matcher

def test_rule1():

    rule = yaml.safe_load(r'''
                      rule_selector: root['routers'][\d+]
                      inventory: all
                      create:
                          - tasks: create_tasks.yml
                      retrieve:
                          - tasks: get_tasks.yml
                      update:
                          - tasks: create_tasks.yml
                      delete:
                          - tasks: del_tasks.yml
                      ''')

def test_rule2():

    rule = yaml.safe_load(r'''
                      rule_selector: root['routers'][\d+]
                      inventory_selector: name
                      create:
                          - role: create_role
                      retrieve:
                          - role: get_role
                      update:
                          - role: update_role
                      delete:
                          - role: delete_role
                      ''')

def test_rules():

    t1 = yaml.safe_load('''
    routers:
        - name: R1
        - name: R2
    ''')

    t2 = yaml.safe_load('''
    routers:
        - name: R1
        - name: R3
    ''')

    rules = yaml.safe_load(r'''
                           rules:
                            - rule_selector: root['routers'][\d+]
                              inventory_selector: name
                           ''')

    diff = DeepDiff(t1, t2)
    assert re.match(make_matcher(r"root['routers'][\d+]"), "root['routers'][1]['name']")


    for rule in rules['rules']:
        matcher = make_matcher(rule['rule_selector'])
        changed_path = list(diff['values_changed'].keys())[0]
        match =  re.match(matcher, changed_path)
        assert match
        changed_subtree_path = match.groups()[0] 
        assert changed_subtree_path == "root['routers'][1]"
        changed_value = extract(t2, changed_path)
        assert changed_value == 'R3'
        changed_subtree = extract(t2, changed_subtree_path)
        assert changed_subtree == {'name': 'R3'}

