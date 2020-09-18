
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
