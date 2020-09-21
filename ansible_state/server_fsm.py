
from gevent_fsm.fsm import State, transitions


class _Start(State):

    @transitions('Ready')
    def start(self, controller):

        controller.changeState(Ready)


Start = _Start()


class _Ready(State):

    def start(self, controller):
        pass


Ready = _Ready()


class _Waiting(State):

    pass


Waiting = _Waiting()
