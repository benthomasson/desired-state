
from deepdiff import DeepDiff, extract

import re
import os

import yaml

from ansible_state.util import make_matcher
from ansible_state.rule import select_rules, select_rules_recursive, Action
from ansible_state.diff import deduplicate_rules, get_rule_action_subtree

from pprint import pprint

HERE = os.path.abspath(os.path.dirname(__file__))


def load_rule(name):
    with open(os.path.join(HERE, 'rules', f'{name}.yml')) as f:
        return yaml.safe_load(f.read())


def load_state(name, version):
    with open(os.path.join(HERE, 'states', name, f'{version}.yml')) as f:
        return yaml.safe_load(f.read())


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

    diff = DeepDiff(t1, t2)
    assert diff == {'values_changed': {"root['routers'][1]['name']": {'new_value': 'R3', 'old_value': 'R2'}}}
    assert re.match(make_matcher(r"root['routers'][\d+]"), "root['routers'][1]['name']")

    assert len(rules['rules']) == 1
    for rule in rules['rules']:
        matcher = make_matcher(rule['rule_selector'])
        changed_path = list(diff['values_changed'].keys())[0]
        match = re.match(matcher, changed_path)
        assert match
        changed_subtree_path = match.groups()[0]
        assert changed_subtree_path == "root['routers'][1]"
        old_value = extract(t1, changed_path)
        assert old_value == 'R2'
        new_value = extract(t2, changed_path)
        assert new_value == 'R3'
        new_subtree = extract(t2, changed_subtree_path)
        assert new_subtree == {'name': 'R3'}
        old_subtree = extract(t1, changed_subtree_path)
        assert old_subtree == {'name': 'R2'}
        changed_value_subpath = changed_path[len(changed_subtree_path):]
        assert changed_value_subpath == "['name']"
        assert rule['inventory_selector'] == "['name']"
        inventory_selector = rule['inventory_selector']
        new_inventory = extract(new_subtree, f"root{inventory_selector}")
        assert new_inventory == 'R3'
        old_inventory = extract(old_subtree, f"root{inventory_selector}")
        assert old_inventory == 'R2'

        # this should be a delete of R2 and a create of R3
        # so just using the DeepDiff change type is not sufficient
        # actually this is fine since we want to be able to support changing
        # the identifier of an object

    matching_rules = select_rules(diff, rules['rules'])
    assert len(matching_rules) == 1
    assert matching_rules[0][2].groups()[0] == "root['routers'][1]"


def test_rules_add():

    t1 = load_state('delete_value', 'B')
    t2 = load_state('delete_value', 'A')
    rules = load_rule('routers_simple')

    diff = DeepDiff(t1, t2)
    assert diff == {'dictionary_item_added': ["root['routers'][0]['interfaces'][0]['ip_address']"]}

    # This should be a change of the subtree since it is adding new elements.
    # It looks like the CRUD operations depend on the matcher.
    # if there is nothing in the old tree but something in the new tree it is a create
    # if there is something new, deleted, or changed in a subtree then it is an update
    # if there is nothing in the new tree but something in the old tree then it is a delete

    assert len(rules['rules']) == 1
    for rule in rules['rules']:
        matcher = make_matcher(rule['rule_selector'])
        changed_path = diff['dictionary_item_added'][0]
        match = re.match(matcher, changed_path)
        changed_subtree_path = match.groups()[0]
        assert changed_subtree_path == "root['routers'][0]"
        try:
            old_value = extract(t1, changed_path)
            assert False, "Did not throw error"
        except KeyError:
            pass
        new_value = extract(t2, changed_path)
        assert new_value == '1.1.1.1'
        new_subtree = extract(t2, changed_subtree_path)
        assert new_subtree == {'name': 'R1', 'interfaces': [{'name': 'eth1', 'ip_address': '1.1.1.1'}]}
        old_subtree = extract(t1, changed_subtree_path)
        assert old_subtree == {'interfaces': [{'name': 'eth1'}], 'name': 'R1'}
        changed_value_subpath = changed_path[len(changed_subtree_path):]

    matching_rules = select_rules(diff, rules['rules'])
    assert len(matching_rules) == 1
    assert matching_rules[0][2].groups()[0] == "root['routers'][0]"


def test_rules_delete():

    t1 = load_state('delete_value', 'A')
    t2 = load_state('delete_value', 'B')
    rules = load_rule('routers_simple')

    diff = DeepDiff(t1, t2)
    assert diff == {'dictionary_item_removed': ["root['routers'][0]['interfaces'][0]['ip_address']"]}

    # This should be a change of the subtree since it is adding new elements.
    # It looks like the CRUD operations depend on the matcher.
    # if there is nothing in the old tree but something in the new tree it is a create
    # if there is something new, deleted, or changed in a subtree then it is an update
    # if there is nothing in the new tree but something in the old tree then it is a delete

    assert len(rules['rules']) == 1
    for rule in rules['rules']:
        matcher = make_matcher(rule['rule_selector'])
        changed_path = diff['dictionary_item_removed'][0]
        match = re.match(matcher, changed_path)
        changed_subtree_path = match.groups()[0]
        assert changed_subtree_path == "root['routers'][0]"
        try:
            new_value = extract(t2, changed_path)
            assert False, "Did not throw error"
        except KeyError:
            pass
        old_value = extract(t1, changed_path)
        assert old_value == '1.1.1.1'
        new_subtree = extract(t2, changed_subtree_path)
        assert new_subtree == {'interfaces': [{'name': 'eth1'}], 'name': 'R1'}
        old_subtree = extract(t1, changed_subtree_path)
        assert old_subtree == {'name': 'R1', 'interfaces': [{'name': 'eth1', 'ip_address': '1.1.1.1'}]}
        changed_value_subpath = changed_path[len(changed_subtree_path):]

    matching_rules = select_rules(diff, rules['rules'])
    assert len(matching_rules) == 1
    assert matching_rules[0][2].groups()[0] == "root['routers'][0]"


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
    current_desired_state = t1
    new_desired_state = t2

    diff = DeepDiff(t1, t2)
    assert diff == {'values_changed': {"root['routers'][0]['name']": {'new_value': 'R2', 'old_value': 'R1'}}}

    rules = load_rule('routers_simple')

    for rule in rules['rules']:
        matcher = make_matcher(rule['rule_selector'])
        changed_path = list(diff['values_changed'].keys())[0]
        match = re.match(matcher, changed_path)
        assert match

    matching_rules = select_rules(diff, rules['rules'])
    assert len(matching_rules) == 1
    assert matching_rules[0][2].groups()[0] == "root['routers'][0]"

    matching_rules = select_rules_recursive(diff, rules['rules'], t1, t2)
    assert len(matching_rules) == 1
    assert matching_rules[0][2].groups()[0] == "root['routers'][0]"

    match = matching_rules[0][2]
    print(match)

    changed_subtree_path = match.groups()[0]

    new_subtree = extract(new_desired_state, changed_subtree_path)
    old_subtree = extract(current_desired_state, changed_subtree_path)


def test_rules_list_insert_element():
    '''
    This case tests insertion into a list.  It should cause one add
    instead of multiple changes.
    '''

    t1 = load_state('add_list_value', 'B')
    t2 = load_state('add_list_value', 'A')
    rules = load_rule('routers_simple')

    diff = DeepDiff(t1, t2)
    assert diff == {'iterable_item_added': {"root['routers'][5]": {'name': 'R6'}},
                    'values_changed': {"root['routers'][1]['name']": {'new_value': 'R2',
                                                                      'old_value': 'R3'},
                                       "root['routers'][2]['name']": {'new_value': 'R3',
                                                                      'old_value': 'R4'},
                                       "root['routers'][3]['name']": {'new_value': 'R4',
                                                                      'old_value': 'R5'},
                                       "root['routers'][4]['name']": {'new_value': 'R5',
                                                                      'old_value': 'R6'}}}

    # The problem here is that it looks like R6 was added and the other ones where changed.
    # This will happen whenever there are any insertions to a list.
    # A work around for this is to remove an item from the list and rerun the diff.
    # The item to remove is the first item that changed.

    new_item = extract(t2, "root['routers'][1]")
    assert new_item == {'name': 'R2'}
    parent = extract(t2, "root['routers']")
    del parent[1]

    diff = DeepDiff(t1, t2)
    assert diff == {}


def test_rules_list_remove_element():
    '''
    This case tests insertion into a list.  It should cause one add
    instead of multiple changes.
    '''

    t1 = load_state('add_list_value', 'A')
    t2 = load_state('add_list_value', 'B')
    rules = load_rule('routers_simple')

    diff = DeepDiff(t1, t2)
    assert diff == {'iterable_item_removed': {"root['routers'][5]": {'name': 'R6'}},
                    'values_changed': {"root['routers'][1]['name']": {'new_value': 'R3',
                                                                      'old_value': 'R2'},
                                       "root['routers'][2]['name']": {'new_value': 'R4',
                                                                      'old_value': 'R3'},
                                       "root['routers'][3]['name']": {'new_value': 'R5',
                                                                      'old_value': 'R4'},
                                       "root['routers'][4]['name']": {'new_value': 'R6',
                                                                      'old_value': 'R5'}}}

    # The problem here is that it looks like R6 was removed and the other ones where changed.
    # This will happen whenever there are any removals from a list.
    # A work around for this is to remove an item from the list and rerun the diff.
    # The item to remove is the first item that changed.

    removed_item = extract(t1, "root['routers'][1]")
    assert removed_item == {'name': 'R2'}
    parent = extract(t1, "root['routers']")
    del parent[1]

    diff = DeepDiff(t1, t2)
    assert diff == {}


def run_diff_get_action(a, b, rules):

    diff = DeepDiff(a, b)
    matching_rules = select_rules_recursive(diff, rules['rules'], a, b)
    dedup_matching_rules = deduplicate_rules(matching_rules)
    action, subtree = get_rule_action_subtree(dedup_matching_rules[0], a, b)
    return action, subtree


def test_rules_dictionary_add_item():
    '''
    This case tests insertion into a list.  It should cause one add
    instead of multiple changes.
    '''

    t1 = load_state('add_dict_value', 'A')
    t2 = load_state('add_dict_value', 'B')
    rules = load_rule('routers_simple')

    diff = DeepDiff(t1, t2)
    matching_rules = select_rules_recursive(diff, rules['rules'], t1, t2)
    dedup_matching_rules = deduplicate_rules(matching_rules)
    action, subtree = get_rule_action_subtree(dedup_matching_rules[0], t1, t2)

    assert action == Action.UPDATE
    assert subtree == {'name': 'R1', 'router-id': '1.1.1.1'}

    action, subtree = run_diff_get_action(t1, t2, rules)

    assert action == Action.UPDATE
    assert subtree == {'name': 'R1', 'router-id': '1.1.1.1'}


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
