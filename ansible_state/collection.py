
import os
import shutil
import subprocess

ANSIBLE_GALAXY = shutil.which('ansible-galaxy')


def find_collection(name):
    if ANSIBLE_GALAXY is None:
        raise Exception('ansible-galaxy is not installed')
    output = subprocess.check_output([ANSIBLE_GALAXY, 'collection', 'list', name])
    output = output.decode()
    parts = name.split('.')
    for line in output.splitlines():
        if line.startswith('# '):
            location = line[2:]
            location = os.path.join(location, *parts)
            if os.path.exists(location):
                return location
    return None



def load_schema(collection, schema):
    pass


def load_rules(collection, rules):
    pass


def load_tasks(collection, tasks):
    pass
