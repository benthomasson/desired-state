
from deepdiff import DeepDiff, extract

import re
import os

import yaml

from ansible_state.util import make_matcher
from ansible_state.rule import select_rules, select_rules_recursive, Action
from ansible_state.diff import deduplicate_rules, get_rule_action_subtree
from ansible_state.transform import transform_state

from pprint import pformat

HERE = os.path.abspath(os.path.dirname(__file__))


def load_rule(name):
    with open(os.path.join(HERE, 'rules', f'{name}.yml')) as f:
        return yaml.safe_load(f.read())


def load_state(name, version):
    with open(os.path.join(HERE, 'states', name, f'{version}.yml')) as f:
        return yaml.safe_load(f.read())


def run_diff_get_action(a, b, rules):

    diff = DeepDiff(a, b, ignore_order=True)
    matching_rules = select_rules_recursive(diff, rules['rules'], a, b)
    dedup_matching_rules = deduplicate_rules(matching_rules)
    assert len(dedup_matching_rules) >= 1, "No rules found"
    assert len(dedup_matching_rules) == 1, "More than on rule found: " + pformat(dedup_matching_rules)
    action, subtree = get_rule_action_subtree(dedup_matching_rules[0], a, b)
    return action, subtree


def run_diff_get_actions(a, b, rules):

    a = transform_state(a, rules)
    b = transform_state(b, rules)

    diff = DeepDiff(a, b, ignore_order=True)
    matching_rules = select_rules_recursive(diff, rules['rules'], a, b)
    dedup_matching_rules = deduplicate_rules(matching_rules)
    return [get_rule_action_subtree(x, a, b) for x in dedup_matching_rules]

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


def test_rules_change():

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
                              inventory_selector: "['name']"
                           ''')


    actions = run_diff_get_actions(t1, t2, rules)

    assert len(actions) == 1
    assert actions[0][0] == Action.UPDATE
    assert actions[0][1] == {'name': 'R3'}


def test_rules_add():

    t1 = load_state('delete_value', 'B')
    t2 = load_state('delete_value', 'A')
    rules = load_rule('routers_simple')

    actions = run_diff_get_actions(t1, t2, rules)

    assert len(actions) == 1
    assert actions[0][0] == Action.UPDATE
    assert actions[0][1] == {'interfaces': [{'ip_address': '1.1.1.1', 'name': 'eth1'}], 'name': 'R1'}


def test_rules_delete():

    t1 = load_state('delete_value', 'A')
    t2 = load_state('delete_value', 'B')
    rules = load_rule('routers_simple')

    actions = run_diff_get_actions(t1, t2, rules)

    assert len(actions) == 1
    assert actions[0][0] == Action.UPDATE
    assert actions[0][1] == {'interfaces': [{'name': 'eth1'}], 'name': 'R1'}


def test_rules_rename():
    '''
    Rules based on position may be able to detect name changes easily since
    the identifier is inside the data structure.  Reordering the data may
    cause unintended name changes.

    Possible solutions include:
        sorting the elements in a list by identifier before detecting changes
    '''

    t1 = load_state('rename_item', 'A')
    t2 = load_state('rename_item', 'B')
    rules = load_rule('routers_simple')

    actions = run_diff_get_actions(t1, t2, rules)

    assert len(actions) == 1
    assert actions[0][0] == Action.UPDATE
    assert actions[0][1] == {'interfaces': [{'ip_address': '1.1.1.1', 'name': 'eth1'}], 'name': 'R2'}


def test_rules_list_insert_element():
    '''
    This case tests insertion into a list.  It should cause one add
    instead of multiple changes.
    '''

    t1 = load_state('add_list_value', 'B')
    t2 = load_state('add_list_value', 'A')
    rules = load_rule('routers_simple')

    actions = run_diff_get_actions(t1, t2, rules)

    assert len(actions) == 1
    assert actions[0][0] == Action.CREATE
    assert actions[0][1] == {'name': 'R2'}


def test_rules_list_remove_element():
    '''
    This case tests insertion into a list.  It should cause one remove
    instead of multiple changes.
    '''

    t1 = load_state('add_list_value', 'A')
    t2 = load_state('add_list_value', 'B')
    rules = load_rule('routers_simple')

    actions = run_diff_get_actions(t1, t2, rules)

    assert len(actions) == 1
    assert actions[0][0] == Action.DELETE
    assert actions[0][1] == {'name': 'R2'}


def test_rules_dictionary_add_item():
    '''
    This case tests insertion into a list.  It should cause one add
    instead of multiple changes.
    '''

    t1 = load_state('add_dict_value', 'A')
    t2 = load_state('add_dict_value', 'B')
    rules = load_rule('routers_simple')

    actions = run_diff_get_actions(t1, t2, rules)

    print(actions)

    assert len(actions) == 1
    assert actions[0][0] == Action.UPDATE
    assert actions[0][1] == {'name': 'R1', 'router-id': '1.1.1.1'}


def test_rules_dictionary_remove_item():
    '''
    This case tests insertion into a list.  It should cause one add
    instead of multiple changes.
    '''

    t1 = load_state('add_dict_value', 'A')
    t2 = load_state('add_dict_value', 'B')
    rules = load_rule('routers_simple')

    action, subtree = run_diff_get_action(t2, t1, rules)

    assert action == Action.UPDATE
    assert subtree == {'name': 'R1'}


def test_empty_add_item():
    '''
    Tests the case to add an item to an empty file.
    '''

    t1 = load_state('empty_add_item', 'A')
    t2 = load_state('empty_add_item', 'B')
    rules = load_rule('routers_simple')

    action, subtree = run_diff_get_action(t1, t2, rules)

    assert action == Action.CREATE
    assert subtree == {'name': 'R1'}


def test_empty_remove_item():
    '''
    Tests the case to remove everything
    '''

    t1 = load_state('empty_add_item', 'B')
    t2 = load_state('empty_add_item', 'A')
    rules = load_rule('routers_simple')

    action, subtree = run_diff_get_action(t1, t2, rules)

    assert action == Action.DELETE
    assert subtree == {'name': 'R1'}


def test_rules_list_insert_element2():
    '''
    This case tests insertion into a list.  It should cause one add
    instead of multiple changes.
    '''

    t1 = load_state('add_list_value', 'B')
    t2 = load_state('add_list_value', 'A')
    rules = load_rule('routers_with_id')

    actions = run_diff_get_actions(t1, t2, rules)

    assert actions[0][0] == Action.CREATE


def test_rules_list_remove_element2():
    '''
    '''

    t1 = load_state('add_list_value', 'A')
    t2 = load_state('add_list_value', 'B')
    rules = load_rule('routers_with_id')

    actions = run_diff_get_actions(t1, t2, rules)

    assert actions[0][0] == Action.DELETE


def test_reorder_list():
    '''
    '''

    t1 = load_state('reorder_list', 'A')
    t2 = load_state('reorder_list', 'B')
    rules = load_rule('routers_with_id')

    actions = run_diff_get_actions(t1, t2, rules)

    assert len(actions) == 0
