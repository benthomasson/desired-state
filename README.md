

# Desired State Configuration

Desired state configuration allows users to focus on what they
want instead of how to make it so.  This simplifies automation
for domain experts and allows automation experts to make generic
operations that will work for many configurations.


# Getting Started

This repository uses [pipenv](https://pypi.org/project/pipenv/) to manage the dependencies. To install
the dependencies for a development environment run the following commands:

    pipenv install --dev

To load the shell for this environment run these commands:

    pipenv shell

To install an example collection use this command:

    ansible-galaxy collection install benthomasson.expect

To run the tests use this command after opening the shell:

    pytest -v



# Code Organization

This project uses event driven programming using finite state machines
to provide deterministic and correct behavior.  This allows the project
to react to external events easily.

The entry point for the CLI commands is located the [cli.py](desired_state/cli.py) file.

Message types between finite state machines are defined in [messages.py](desired_state/messages.py).

The reconciliation loop is defined as a finite state machine in
[reconciliation_fsm.py](desired_state/reconciliation_fsm.py)

The main monitor process which contains the reconciliation loop is defined
in [monitor.py](desired_state/monitor.py)

The generation of playbooks based on the differences between states is defined in [diff.py](desired_state/diff.py).

Selection of appropriate change rules based on state diff is defined in [rule.py](desired_state/rule.py)

A client/server implementation for injecting desired state into the monitor process is defined
in the [client.py](desired_state/client.py) and [server.py](desired_state/server.py) files.

Collection support is defined in [collection.py](desired_state/collection.py).

Streaming telemetry is defined in [stream.py](desired_state/stream.py).

State schema validation is provided in [validate.py](desired_state/validate.py).

