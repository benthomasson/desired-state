
A desired state system for Ansible.


Experiments in desired state:

v0. playbook resolution loop: watch a desired state file for changes and then run a playbook passing the changes to the playbook.
v1. diff and rules: accept two versions of a desired state file and diff, then select rules and build a playbook based on the diff
v2. full resolution loop: implement a resolution loop finite state machine and use diff of desired state and rules from v1 to build the playbook
v3. planner: Consolidate all the changes between two versions of state into one playbook/project.
             Add an option to export that project to Tower instead of runner.
v4. validation:  Add operational state validation to the rules and to the finite state machine
v5. streaming telemetry:  Export data over a channel to external consumers




