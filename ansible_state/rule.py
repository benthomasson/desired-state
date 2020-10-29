

import re
from .util import make_matcher
from enum import Enum
from deepdiff import extract

from pprint import pprint

class Action(Enum):

    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    RETRIEVE = 'RETRIEVE'
    DELETE = 'DELETE'
    RENAME = 'RENAME'
    VALIDATE = 'VALIDATE'


ACTION_RULES = {Action.CREATE: 'create',
                Action.UPDATE: 'update',
                Action.RETRIEVE: 'retrieve',
                Action.DELETE: 'delete',
                Action.RENAME: 'rename',
                Action.VALIDATE: 'validate'}


def select_rules_recursive(diff, rules, current_desired_state, new_desired_state):

    matching_rules = []
    matchers = [(make_matcher(rule['rule_selector']), rule) for rule in rules]

    for key, value in diff.get('values_changed', {}).items():
        for (matcher, rule) in matchers:
            match = re.match(matcher, key)
            if match:
                matching_rules.append(('values_changed', rule, match, value))

    for item in diff.get('dictionary_item_added', []):
        pprint(diff)
        print('dictionary_item_added', item)
        for (matcher, rule) in matchers:
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('dictionary_item_added', rule, match, None))
            new_subtree = extract(new_desired_state, item)
            print(new_subtree)
            select_rules_recursive_helper(diff, matchers, matching_rules, item, new_subtree)

    for item in diff.get('dictionary_item_removed', []):
        for (matcher, rule) in matchers:
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('dictionary_item_removed', rule, match, None))

    for item in diff.get('iterable_item_added', []):
        for (matcher, rule) in matchers:
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('iterable_item_added', rule, match, None))

    for item in diff.get('iterable_item_removed', []):
        for (matcher, rule) in matchers:
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('iterable_item_removed', rule, match, None))

    for key, value in diff.get('type_changes', {}).items():
        # Handles case in YAML where an empty list defaults to None type
        if value.get('old_type') == type(None) and value.get('new_type') == list:
            # Add a single new element to the key
            # TODO: this should probably loop over all the new elements in the list not just one
            key += '[0]'
        elif value.get('old_type') == list and value.get('new_type') == type(None):
            # Add a single new element to the key
            key += '[0]'
        for (matcher, rule) in matchers:
            match = re.match(matcher, key)
            if match:
                matching_rules.append(('type_changes', rule, match, None))

        # Handles case in YAML where an empty dict defaults to None type
        if value.get('old_type') == type(None) and value.get('new_type') == dict:
            # Try the matcher against all the keys in the dict
            for dict_key in value.get('new_value').keys():
                new_key = f"{key}['{dict_key}']"
                for (matcher, rule) in matchers:
                    match = re.match(matcher, new_key)
                    if match:
                        matching_rules.append(('type_changes', rule, match, None))
            select_rules_recursive_helper(diff, matchers, matching_rules, key, value.get('new_value'))

    return matching_rules


def select_rules_recursive_helper(diff, matchers, matching_rules, path, value):

    print(path)

    for (matcher, rule) in matchers:
        match = re.match(matcher, path)
        if match:
            print('match')
            matching_rules.append(('subtree', rule, match, value))


    if type(value) is list:
        for i, item in enumerate(value):
            select_rules_recursive_helper(diff, matchers, matching_rules, f"{path}[{i}]", item)

    if type(value) is dict:
        for k, v in value.items():
            select_rules_recursive_helper(diff, matchers, matching_rules, f"{path}['{k}']", v)




def select_rules(diff, rules):
    matching_rules = []
    for rule in rules:
        matcher = make_matcher(rule['rule_selector'])
        for key, value in diff.get('values_changed', {}).items():
            match = re.match(matcher, key)
            if match:
                matching_rules.append(('values_changed', rule, match, value))
        for item in diff.get('dictionary_item_added', []):
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('dictionary_item_added', rule, match, None))
        for item in diff.get('dictionary_item_removed', []):
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('dictionary_item_removed', rule, match, None))
        for item in diff.get('iterable_item_added', []):
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('iterable_item_added', rule, match, None))
        for item in diff.get('iterable_item_removed', []):
            match = re.match(matcher, item)
            if match:
                matching_rules.append(('iterable_item_removed', rule, match, None))
        for key, value in diff.get('type_changes', {}).items():
            # Handles case in YAML where an empty list defaults to None type
            if value.get('old_type') == type(None) and value.get('new_type') == list:
                # Add a single new element to the key
                # TODO: this should probably loop over all the new elements in the list not just one
                key += '[0]'
            elif value.get('old_type') == list and value.get('new_type') == type(None):
                # Add a single new element to the key
                key += '[0]'
            match = re.match(matcher, key)
            if match:
                matching_rules.append(('type_changes', rule, match, None))

            # Handles case in YAML where an empty dict defaults to None type
            if value.get('old_type') == type(None) and value.get('new_type') == dict:
                # Try the matcher against all the keys in the dict
                for dict_key in value.get('new_value').keys():
                    new_key = f"{key}['{dict_key}']"
                    match = re.match(matcher, new_key)
                    if match:
                        matching_rules.append(('type_changes', rule, match, None))


    return matching_rules
