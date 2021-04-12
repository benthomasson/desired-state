
from gevent_fsm.fsm import State, transitions


class _Start(State):

    @transitions('Ready')
    def start(self, controller):

        controller.changeState(Ready)


Start = _Start()


class _Ready(State):

    def start(self, controller):
        print("server_fsm buffered_messages", len(
            controller.context.buffered_messages))
        if not controller.context.buffered_messages.empty():
            controller.context.queue.put(
                controller.context.buffered_messages.get())

    def onServiceInstance(self, controller, message_type, message):
        print(message)
        controller.context.start_or_update_monitor(message)


Ready = _Ready()


class _Waiting(State):

    pass


Waiting = _Waiting()
