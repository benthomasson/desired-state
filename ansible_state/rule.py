

import re
from .util import make_matcher


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
            print(value)
            if value.get('old_type') == type(None) and value.get('new_type') == list:
                key += '[0]'
            elif value.get('old_type') == list and value.get('new_type') == type(None):
                key += '[0]'
            match = re.match(matcher, key)
            if match:
                matching_rules.append(('type_changes', rule, match, None))
    return matching_rules
