Ansible Desired State Documenation
==================================


About Ansible Desired State
```````````````````````````

Ansible desired state allows you automate your systems by telling
the automation what state you want that system to be in.   Ansible
desired state will detect the differences in the state of the system
and make only the changes that are necessary to acheive your desired
state.

This makes Ansible much more powerful and scalable that using playbooks
or roles that will touch every host and run every task  every time they
are run.

Ansible desired state reads state definition files and calculates
the difference between the current state and the new desired state.
Then Ansible desired state uses change rules to determine how to make
the system reflect the desired state.  Ansible desired state is completely
customizable and you can define the state definition using any valid
YAML file.  The YAML file should be a description of your system.
If you have used Ansible previous think of a vars file as your description file.

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
