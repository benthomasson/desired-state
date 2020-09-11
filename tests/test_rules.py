
from deepdiff import DeepDiff, extract

import re

import yaml

from ansible_state.util import make_matcher
from ansible_state.rule import select_rules

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
        match =  re.match(matcher, changed_path)
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

    matching_rules = select_rules(diff, rules['rules'])
    assert len(matching_rules) == 1
    assert matching_rules[0][2].groups()[0] == "root['routers'][1]"


def test_rules_add():

    t1 = yaml.safe_load('''
    routers:
        - name: R1
          interfaces:
            - name: eth1
    ''')

    t2 = yaml.safe_load('''
    routers:
        - name: R1
          interfaces:
            - name: eth1
              ip_address: 1.1.1.1
    ''')

    rules = yaml.safe_load(r'''
                           rules:
                            - rule_selector: root['routers'][\d+]
                              inventory_selector: "['name']"
                           ''')

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
        match =  re.match(matcher, changed_path)
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

    t1 = yaml.safe_load('''
    routers:
        - name: R1
          interfaces:
            - name: eth1
              ip_address: 1.1.1.1
    ''')

    t2 = yaml.safe_load('''
    routers:
        - name: R1
          interfaces:
            - name: eth1
    ''')

    rules = yaml.safe_load(r'''
                           rules:
                            - rule_selector: root['routers'][\d+]
                              inventory_selector: "['name']"
                           ''')

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
        match =  re.match(matcher, changed_path)
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

