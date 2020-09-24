from gevent_fsm.fsm import State, transitions

import yaml
from deepdiff import DeepDiff
from .diff import ansible_state_diff, ansible_state_discovery
from pprint import pprint


class _Discover1(State):

    @transitions('Diff2')
    def start(self, controller):

        # Trivial discovery
        # Assume the state is the same as new desired state

        monitor = controller.context

        monitor.discovered_system_state = ansible_state_discovery(monitor.secrets,
                                                                  monitor.project_src,
                                                                  monitor.current_desired_state,
                                                                  monitor.new_desired_state,
                                                                  monitor.ran_rules,
                                                                  monitor.inventory,
                                                                  False)
        controller.changeState(Diff2)


Discover1 = _Discover1()


class _Help(State):

    pass


Help = _Help()


class _Resolve1(State):

    @transitions('Discover1')
    @transitions('Retry')
    def start(self, controller):

        monitor = controller.context

        monitor.ran_rules = ansible_state_diff(monitor.secrets,
                                               monitor.project_src,
                                               monitor.current_desired_state,
                                               monitor.new_desired_state,
                                               monitor.rules,
                                               monitor.inventory,
                                               False)

        if all([x[4] for x in monitor.ran_rules]):
            controller.changeState(Discover1)
        else:
            controller.changeState(Retry)


Resolve1 = _Resolve1()


class _Resolve2(State):

    @transitions('Discover1')
    @transitions('Retry')
    def start(self, controller):

        monitor = controller.context

        result = ansible_state_diff(monitor.secrets,
                                    monitor.project_src,
                                    monitor.discovered_system_state,
                                    monitor.new_desired_state,
                                    monitor.rules,
                                    monitor.inventory,
                                    False)

        if result:
            controller.changeState(Discover1)
        else:
            controller.changeState(Retry)


Resolve2 = _Resolve2()


class _Resolve3(State):

    @transitions('Discover1')
    @transitions('Retry')
    def start(self, controller):

        monitor = controller.context

        result = ansible_state_diff(monitor.secrets,
                                    monitor.project_src,
                                    monitor.discovered_system_state,
                                    monitor.current_desired_state,
                                    monitor.rules,
                                    monitor.inventory,
                                    False)

        if result:
            controller.changeState(Discover2)
        else:
            controller.changeState(Retry)


Resolve3 = _Resolve3()


class _Waiting(State):

    def start(self, controller):
        print("resolution_fsm buffered_messages", len(controller.context.buffered_messages))
        if not controller.context.buffered_messages.empty():
            controller.context.queue.put(controller.context.buffered_messages.get())

    @transitions('Diff1')
    def onDesiredState(self, controller, message_type, message):
        print('Waiting.onDesiredState')
        controller.context.new_desired_state = yaml.safe_load(message.desired_state)
        controller.changeState(Diff1)

    @transitions('Diff1')
    def onSystemState(self, controller, message_type, message):
        print('Waiting.onSystemState')
        controller.context.discovered_system_state = yaml.safe_load(message.system_state)
        controller.changeState(Diff3)

    @transitions('Discover2')
    def onPoll(self, controller, message_type, message):
        controller.changeState(Discover2)


Waiting = _Waiting()


class _Diff1(State):

    @transitions('Resolve1')
    @transitions('Waiting')
    def start(self, controller):
        controller.context.diff = DeepDiff(controller.context.current_desired_state, controller.context.new_desired_state)
        pprint(controller.context.diff)

        if controller.context.diff:
            controller.changeState(Resolve1)
        else:
            controller.changeState(Waiting)


Diff1 = _Diff1()


class _Revert(State):

    @transitions('Help')
    def failure(self, controller, message_type, message):

        controller.changeState(Help)

    @transitions('Discover1')
    def success(self, controller, message_type, message):

        controller.changeState(Discover1)


Revert = _Revert()


class _Diff3(State):

    @transitions('Resolve3')
    @transitions('Waiting')
    def start(self, controller):
        controller.context.diff = DeepDiff(controller.context.discovered_system_state, controller.context.current_desired_state)
        print(controller.context.diff)

        if controller.context.diff:
            controller.changeState(Resolve3)
        else:
            controller.changeState(Waiting)


Diff3 = _Diff3()


class _Discover2(State):

    @transitions('Diff3')
    def start(self, controller):

        # Trivial discovery
        # Assume the state is the same as current desired state
        controller.context.discovered_system_state = controller.context.current_desired_state
        controller.changeState(Diff3)


Discover2 = _Discover2()


class _Start(State):

    @transitions('Waiting')
    def start(self, controller):
        controller.changeState(Waiting)


Start = _Start()


class _Diff2(State):

    @transitions('Resolve2')
    @transitions('Waiting')
    def start(self, controller):
        controller.context.diff = DeepDiff(controller.context.new_desired_state, controller.context.discovered_system_state)
        print(controller.context.diff)

        if controller.context.diff:
            controller.changeState(Resolve2)
        else:
            controller.context.current_desired_state = controller.context.new_desired_state
            controller.changeState(Waiting)


Diff2 = _Diff2()


class _Retry(State):

    @transitions('Revert')
    def failure(self, controller, message_type, message):

        controller.changeState(Revert)

    @transitions('Discover1')
    def success(self, controller, message_type, message):

        controller.changeState(Discover1)


Retry = _Retry()
