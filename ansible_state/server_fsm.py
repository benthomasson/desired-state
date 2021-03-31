
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

    def onDesiredState(self, controller, message_type, message):
        print('onDesiredState')
        controller.context.outbox.put(message)

    def onActualState(self, controller, message_type, message):
        print('onActualState')
        controller.context.outbox.put(message)


Ready = _Ready()


class _Waiting(State):

    pass


Waiting = _Waiting()
