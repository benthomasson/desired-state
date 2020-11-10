
from deepdiff import DeepDiff, extract

import re


def transform_state(state, rules):
    '''
    transforms the state in place into a form that is easier to compare with DeepDiff
    '''
    # We might want to copy the state here instead of transforming in place
    # transform #1: sort all lists that match rules with the id_key attribute
    for rule in rules['rules']:
        if 'id_key' in rule:
            id_key = rule['id_key']
            rule_selector = rule['rule_selector']
            #Does the rule match a list?
            if rule_selector.endswith(r'[\d+]'):
                # pop off the list regex
                rule_selector = rule_selector[0:-len(r'[\d+]')]
                # get the parent object and the key for later
                parent, _, key = rule_selector.rpartition('[')
                key = key[0:-1]
                key = key.strip('\'')
                parent = extract(state, rule_selector.rpartition('[')[0])
                # get the original value
                value = extract(state, rule_selector)
                if isinstance(value, list):
                    # add the sorted list to the parent using the key
                    parent[key] = sorted(value, key=lambda x: x[id_key])
    return state
