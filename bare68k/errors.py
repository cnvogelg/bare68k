
class Bare68kException(Exception):

    def __init__(self, msg=None):
        Exception.__init__(self, msg)


class ConfigError(Bare68kException):

    def __init__(self, msg=None):
        Bare68kException.__init__(self, msg)


class InternalError(Bare68kException):

    def __init__(self, msg=None):
        Bare68kException.__init__(self, msg)
