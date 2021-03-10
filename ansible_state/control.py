

class AnsibleStateControl(object):

    '''
    A control is a green thread FSM that controls multiple monitors (monitor.py) in one or more
    systems.   Each system is managed by one or more monitors and is defined by a set of desired
    state configurations.  A set of desired state configurations that work together defines a system.
    For instance a set of linux, networking, and application desired state configurations would
    define a system in this terminology.  The control would bring up the linux, networking, and
    application configurations in the correct order to bring the system from zero to a completely
    working application.
    '''

    def __init__(self):
        pass


