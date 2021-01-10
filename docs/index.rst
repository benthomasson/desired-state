Ansible Desired State Documenation
==================================


About Ansible Desired State
```````````````````````````

Ansible desired state allows you automate your systems by telling
the automation what state you want that system to be in.   Ansible
desired state will detect the differences in the state of the system
and make only the changes that are necessary to acheive your desired
state.

This makes Ansible much more powerful and scalable than using playbooks
or roles that will touch every host and run every task  every time they
are run.

Ansible desired state reads state definition files and calculates
the difference between the current state and the new desired state.
Then Ansible desired state uses change rules to determine how to make
the system reflect the desired state.  Ansible desired state is completely
customizable and you can define the state definition using any valid
YAML file.  The YAML file should be a description of your system.
If you have used Ansible previously think of a vars file as your state description file.

Instead of the playbook or role, the state description file is the main
file that you will edit, read, and share with your colleagues.  It should
be understandable by anyone, not just people who have used Ansible before.
YAML syntax is easy to read and moderately easy to write and edit given
an editor that helps with the spacing.

Change rules tell Ansible desired state what to do when a part of the
state description changes.  The change rules `fire` when they match
something that has changed in the state of the system or in the desired
state.  When the rule `fires` it will run a series of tasks or a role
to automatically remedy the difference in state.

Getting Started with Desired State and Collections
``````````````````````````````````````````````````

Collections and desired state work together to provide an
easy way to get started with declarative automation.  This
is useful for the domain expert persona who doesn't need
to understand how to write Ansible playbooks, roles, or
collections.

Collections that support desired state will have one
or more desired state `schema` files that describe
the states that work with the changes rules in that
collection.  The `schema` is a YAML format of the
https://json-schema.org syntax.  It is not necessary
to understand JSON schema as examples of the state
should be sufficient to get started and these should
be found in the documentation for that collection.


To get started with desired state using a collection
install that collection using `ansible-galaxy`.

.. code-block:: bash

    $ ansible-galaxy collection install benthomasson.desired_state

Then write an initial state file of your system using
an example from the collection similar to `initial_state.yml`.


initial_state.yml

.. code-block:: yaml

  schema: benthomasson.desired_state.network_schema
  rules: benthomasson.desired_state.network_rules
  hosts:
  - name: host1


Then start the ansible state monitor process that will watch for
changes in the system state and listen for changes in the desired state.

.. code-block:: bash

    $ ansible-state monitor initial_state.yml rules.yml --inventory inventory.yml


Now write a new version of the desired state with the changes that we want to
make.

desired_state.yml

.. code-block:: yaml

  schema: benthomasson.desired_state.network_schema
  rules: benthomasson.desired_state.network_rules
  hosts:
  - name: host1
    interfaces:
      - name: eth1
        address: 192.168.98.1
        mask: 255.255.255.0


Then in another window update the desired state by sending a message to the monitor process.

.. code-block:: bash

    $ ansible-state update-desired-state desired_state.yml

This will calculate the changes that need to made to your system, update the system,
and verify that it is working correctly.


If you've Ansible before this should feel familar.  The state file is just a vars
file and the format is only limited by the schema in the collection.   If there
isn't a collection yet that 

Getting Started with Desired State without a Collection
``````````````````````````````````````````````````````

initial_state.yml

.. code-block:: yaml

  hosts:
  - name: host1

desired_state.yml

.. code-block:: yaml

  hosts:
  - name: host1
    interfaces:
      - name: eth1
        address: 192.168.98.1
        mask: 255.255.255.0

rules.yml

.. code-block:: yaml

  rules:
  - rule_selector: root.hosts.index
    inventory_selector: node.name
    create:
      tasks: create_host.yml
    update:
      tasks: update_host.yml
    delete:
      tasks: delete_host.yml
    retrieve:
      tasks: discover_host.yml
    validate:
      tasks: validate_host.yml

create_host.yml

.. code-block:: yaml

	- shell:
		cmd: "ifconfig {{item.name}} {{item.address}} netmask {{item.mask}} up"
	  with_items: "{{node.interfaces}}"
	- hostname:
		name: "{{inventory_hostname}}"

.. code-block:: bash

    $ ansible-state monitor initial_state.yml rules.yml --inventory inventory.yml

.. code-block:: bash

    $ ansible-state update-desired-state desired_state.yml

Creating your own Desired State Enabled Collection
``````````````````````````````````````````````````

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   readme
   installation
   usage
   modules
   contributing
   authors
   history

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
