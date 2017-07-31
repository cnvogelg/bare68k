from __future__ import print_function

try:
    # get real extension
    import bare68k.machine as mach
except ImportError:
    # mock mach for doc purposes
    import mock
    mach = mock.Mock()
    print("bare68k is mocked!")
