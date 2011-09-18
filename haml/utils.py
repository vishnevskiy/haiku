import re

def indent(line, indentation):
    if not indentation:
        return line
    
    spaces = ''.join([' ' for _ in xrange(indentation)])
    return spaces + line

def indentation(haml):
    return len(haml) - len(haml.lstrip())

_XHTML_ESCAPE_RE = re.compile('[&<>"]')
_XHTML_ESCAPE_DICT = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}
def xhtml_escape(value):
    """Escapes a string so it is valid within XML or XHTML."""

    if isinstance(value, str):
        value = value.decode('utf-8')
    elif not isinstance(value, unicode):
        value = str(value)

    return _XHTML_ESCAPE_RE.sub(lambda match: _XHTML_ESCAPE_DICT[match.group(0)], value)