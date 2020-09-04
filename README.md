
A desired state system for Ansible.


Experiments in desire state:

v0. playbook resolution loop: watch a desired state file for changes and then run a playbook passing the changes to the playbook.
v1. dynamic playbook resolution loop: watch a desired state file for changes and then generate a playbook to resolve the changes.
v2. event driven resolution loop: listen for changes from external systems and then generate a playbook to resolve the changes.
v3. polling/parsing resolution loop: poll external systems for state and build the state using parsers then generate a playbook to resolve the differences between desired state and actual state.




