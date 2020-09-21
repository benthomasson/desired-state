from gevent_fsm.fsm import State, transitions


class _Discover1(State):

    @transitions('Diff2')
    def complete(self, controller, message_type, message):

        controller.changeState(Diff2)


Discover1 = _Discover1()


class _Help(State):

    pass


Help = _Help()


class _Resolve(State):

    @transitions('Retry')
    def failure(self, controller, message_type, message):

        controller.changeState(Retry)

    @transitions('Discover1')
    def success(self, controller, message_type, message):

        controller.changeState(Discover1)


Resolve = _Resolve()


class _Waiting(State):

    @transitions('Diff1')
    def new_desired_state(self, controller, message_type, message):

        controller.changeState(Diff1)

    @transitions('Discover2')
    def poll(self, controller, message_type, message):

        controller.changeState(Discover2)


Waiting = _Waiting()


class _Diff1(State):

    @transitions('Resolve')
    def difference(self, controller, message_type, message):

        controller.changeState(Resolve)

    @transitions('Waiting')
    def no_difference(self, controller, message_type, message):

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

    @transitions('Resolve')
    def difference(self, controller, message_type, message):

        controller.changeState(Resolve)

    @transitions('Waiting')
    def no_difference(self, controller, message_type, message):

        controller.changeState(Waiting)


Diff3 = _Diff3()


class _Discover2(State):

    @transitions('Diff3')
    def complete(self, controller, message_type, message):

        controller.changeState(Diff3)


Discover2 = _Discover2()


class _Start(State):

    @transitions('Waiting')
    def enter(self, controller, message_type, message):

        controller.changeState(Waiting)


Start = _Start()


class _Diff2(State):

    @transitions('Resolve')
    def difference(self, controller, message_type, message):

        controller.changeState(Resolve)

    @transitions('Waiting')
    def no_difference(self, controller, message_type, message):

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
