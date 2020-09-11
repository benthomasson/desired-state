

import yaml

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

    rules = yaml.safe_load(r'''
                           rules:
                            - rule_selector: root['routers'][\d+]
                              inventory_selector: name
                           ''')
