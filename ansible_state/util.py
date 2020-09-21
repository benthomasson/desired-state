
from itertools import count

# Escape the pattern with a limited set of regexp special characters
# To allow some of the regexps to be used.
# This might now work out in the long term
# We might want to use glob pattern matching or something simple like that
_special_chars_map = {i: '\\' + chr(i) for i in b'()[]{}-|^$.&~# \t\n\r\v\f'}

def escape(pattern):
    return pattern.translate(_special_chars_map)

def make_matcher(pattern):
    pattern = escape(pattern)
    return f'^({pattern}).*$'

def ensure_directory(d):
    if not os.path.exists(d):
        os.mkdir(d)



class ConsoleTraceLog(object):

    def __init__(self):
        self.counter = count(start=1, step=1)

    def trace_order_seq(self):
        return next(self.counter)

    def send_trace_message(self, message):
        print(message)
