Desired State Documenation
==================================


About Desired State
---------------------------

Desired state allows you automate your systems by telling
the automation what state you want that system to be in.   
Desired state will detect the differences in the state of the system
and make only the changes that are necessary to acheive your desired
state.

This makes Ansible much more powerful and scalable than using playbooks
or roles that will touch every host and run every task  every time they
are run.

Desired state reads state definition files and calculates
the difference between the current state and the new desired state.
Then desired state uses change rules to determine how to make
the system reflect the desired state.  Desired state is completely
customizable and you can define the state definition using any valid
YAML file.  The YAML file should be a description of your system.
If you have used Ansible previously think of a vars file as your state description file.

Instead of the playbook or role, the state description file is the main
file that you will edit, read, and share with your colleagues.  It should
be understandable by anyone, not just people who have used Ansible before.
YAML syntax is easy to read and moderately easy to write and edit given
an editor that helps with the spacing.

Change rules tell desired state what to do when a part of the
state description changes.  The change rules `fire` when they match
something that has changed in the state of the system or in the desired
state.  When the rule `fires` it will run a series of tasks or a role
to automatically remedy the difference in state.

Getting Started with Desired State and Collections
--------------------------------------------------

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


**initial_state.yml**

.. code-block:: yaml

  schema: benthomasson.desired_state.network_schema
  rules: benthomasson.desired_state.network_rules


You'll also need an inventory file so Ansible can talk to the hosts.

**inventory.yml**

.. code-block:: yaml

	all:
	  hosts:
		host1:


Then start the ansible state monitor process that will watch for
changes in the system state and listen for changes in the desired state.

.. code-block:: bash

    $ desired-state monitor initial_state.yml --inventory inventory.yml


Now write a new version of the desired state with the changes that we want to
make.

**desired_state.yml**

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

    $ desired-state update-desired-state desired_state.yml

This will calculate the changes that need to made to your system, update the system,
and verify that it is working correctly.


If you've Ansible before this should feel familar.  The state file is just a vars
file and the format is only limited by the schema in the collection.   If there
isn't a collection yet that supports the system you'd like to automate then
you can write your own change rules.


Getting Started with Desired State without a Collection
-------------------------------------------------------

There may not be a collection that supports the system that you want
to automate.  In that case you can build your own change rules to
automate the system.

This section requires the domain expert persona and the automation developer
persona to work together to define a state structure, change rules, and tasks
or roles that will automate their target domain.   Sometimes
the domain expert persona and automation developer persona maybe the
same person but that is not required for desired state.

The domain expert persona can produce a state structure that captures the
state of the system.  The automation developer persona can take that state
structure and build the change rules needed i.e. create, update, delete from
it.

You'll need an initial state file and an inventory to get started.

**initial_state.yml**

.. code-block:: yaml

    # the simplest state is an empty file

**inventory.yml**

.. code-block:: yaml

	all:
	  hosts:
		host1:


Then define a full desired state would look like for your system.


**desired_state.yml**

.. code-block:: yaml

  hosts:
  - name: host1
    interfaces:
      - name: eth1
        address: 192.168.98.1
        mask: 255.255.255.0

Then we need to write change rules that will be used when
changes are detected in the state.  You are free to make the
rules as general or granular as needed. 

These rules detect when a new host is added, removed, or changed and configures
it accordingly.  You can provide tasks or roles for the five operations:
create, retrieve, update, delete, and validate which can be abbreviated as CRUDV.

**rules.yml**

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


The tasks or roles needed for a CRUDV operation can be very simple because
they only need to know how to do one thing.   Also the subtree of the state
file is given to the task as `node` which eliminates all data manipulation
and lookups that complicate Ansible playbooks.

Here we configure the hostname of the host and IP address of all interfaces
on that host.

**create_host.yml**

.. code-block:: yaml

	- shell:
		cmd: "ifconfig {{item.name}} {{item.address}} netmask {{item.mask}} up"
	  with_items: "{{node.interfaces}}"
	- hostname:
		name: "{{inventory_hostname}}"


One we have the state and change rules defined we can start the ansible state
monitor process with an initial state, the rules, and inventory.

.. code-block:: bash

    $ desired-state monitor initial_state.yml rules.yml --inventory inventory.yml


To make changes to the system we send the full desired state and the changes
from the initial state will be calculated, updates to the system will be made,
and validation will be run if any is provided.

.. code-block:: bash

    $ desired-state update-desired-state desired_state.yml

Creating your own Desired State Enabled Collection
``````````````````````````````````````````````````

Once you have change rules that sufficiently automate the changes
that might be made to your system, you can package up those rules
and tasks or roles with a schema and create your own desired
state collection.

You'll need a schema that describes the state structure that your
change rules expect.  This schema should be in JSON schema syntax
using a YAML format.

Schemas are used to check the structure of the inital state and updates to the
desired state.  The can be as strict or lenient as allowed by the change rules.
Stricter schemas will prevent errors while running the change rules.

This example shows a simple schema for a state that expects a list (aka array)
of hosts.

**schema.yml**

.. code-block:: yaml

	---
	type: object
	properties:
	  hosts:
		type: array
		items:
		  $ref: '#/definitions/host'
	definitions:
	  host:
		type: object
	...


Ansible desired state expects change rules, schemas, and tasks
to be found in certain locations in the collection.  Rules should
be placed in a `rules` directory.  Schemas should be placed in a
`schemas` directory.  Tasks should be placed in a `tasks` directory.

You can create a new collection using `ansible-galaxy`.


.. code-block:: bash

    $ ansible-galaxy collection init your_namespace.your_desired_state
    $ cd your_namespace/your_desired_state/
    $ mkdir rules schemas tasks

Then copy the rules file into `rules`, the schema file into `schemas`, and
the tasks into `tasks`.

The rules file should change the location of the tasks to be a collection
specifier of your_namespace.your_desired_state.TASK_NAME.  This will
allow desired state to load the tasks from the collection instead of
from the local directory.

**rules/rules.yml**

.. code-block:: yaml

  rules:
  - rule_selector: root.hosts.index
    inventory_selector: node.name
    create:
      tasks: your_namespace.your_desired_state.create_host
    update:
      tasks: your_namespace.your_desired_state.update_host
    delete:
      tasks: your_namespace.your_desired_state.delete_host
    retrieve:
      tasks: your_namespace.your_desired_state.discover_host
    validate:
      tasks: your_namespace.your_desired_state.validate_host


Then build your collection and publish it to ansible-galaxy.

.. code-block:: bash

    $ ansible-galaxy collection build
    $ ansible-galaxy collection publish your_namespace-your_desired_state-1.0.0.tar.gz --token=...


Then you can install your collection and use it as you would any other collection.

.. code-block:: bash

    $ ansible-galaxy collection install your_namespace.your_desired_state

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
