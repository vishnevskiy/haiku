from .constants import OPERATORS
from . import utils
import re

_AUTOCLOSE = ('meta', 'img', 'link', 'br', 'hr', 'input', 'area', 'param', 'col', 'base',)
_HAML_REGEX = re.compile(
    r'(?P<tag>%\w+)?'
    r'(?P<id>#[:_\w-]*)?'
    r'(?P<class>\.[:\w\.-]*)*'
    r'(?P<attributes>\(.*\))?'
    r'(?P<dict>\{.*\})?'
    r'(?P<innerstrip><)?'
    r'(?P<outerstrip>>)?'
    r'(?P<autoclose>/)?'
    r'(?P<evaluate>=)?'
    r'(?P<content>[^\w\.#\{].*)?'
)
_NEWLINE = '\n'

class HTMLElement(object):
    def __init__(self, node):
        self.node = node

        self.tag = None
        self.id = None
        self.classes = None
        self.autoclose = False
        self.evaluate = False
        self.content = ''

        self._parse_haml_line(node.haml)

    def get_attributes(self):
        attributes = []

        if self.id:
            attributes.append('id="%s"' % self.id)

        if self.classes:
            attributes.append('class="%s"' % ' '.join(self.classes))

        for k, v in self.attributes.items():
            v = self._get_html_value(v)

            if v:
                attributes.append('%s="%s"' % (k, v))

        return ' '.join(attributes)

    def _parse_haml_line(self, haml):
        groups = _HAML_REGEX.search(haml).groupdict('')

        # Decide HTML Tag
        self.tag = groups.get('tag').strip(OPERATORS['element']) or 'div'

        # Parse Atttributes
        attributes = groups.get('dict')
        self.attributes = eval(attributes) if attributes else {}

        attributes = groups.get('attributes')

        if attributes:
            carry = []

            for pair in attributes[1:-1].split(' ')[::-1]:
                parts = map(str.strip, pair.partition('='))
                k, eq, v = parts

                if not eq and not v:
                    carry.append(k)
                    continue

                if carry:
                    carry.append(v)
                    v = ' '.join(carry[::-1])
                    carry = []

                if not v:
                    continue

                if not (v.startswith('"') or v.startswith("'")):
                    if not v.isdigit():
                        v = '= ' + v
                else:
                    v = v[1:-1]

                self.attributes[k] = v

        # Parse Elemnt Id
        self.id = [groups.get('id', '').lstrip(OPERATORS['id'])]

        if 'id' in self.attributes:
            if isinstance(self.attributes['id'], (list, tuple)):
                self.id.append(self.attributes['id'])
            else:
                self.id.append(self.attributes['id'])

            del self.attributes['id']

        self.id = '_'.join(self._flatten(self.id))

        # Parse Classes
        self.classes = set()

        if 'class' in self.attributes:
            for class_ in self._flatten(self.attributes['class']):
                if class_:
                    self.classes.add(class_)

            del self.attributes['class']

        for class_ in groups.get('class').lstrip(OPERATORS['class']).split('.'):
            if class_:
                self.classes.add(class_)

        self.classes = sorted(self.classes)

        self.autoclose = not not groups.get('autoclose') or self.tag in _AUTOCLOSE
        self.innerstrip = not not groups.get('innerstrip')
        self.outerstrip = not not groups.get('outerstrip')
        self.evaluate = not not groups.get('evaluate')
        self.content = groups.get('content').strip()

    def _get_html_value(self, v):
        if not v:
            return ''

        if isinstance(v, (str, unicode)) and v and v[0] == OPERATORS['evaluate']:
            return self.node.parser.target.eval(v.lstrip(OPERATORS['evaluate']).strip())

        v = str(v)

        if '#{' in v or '{%' in v or '{{' in v or '<%' in v:
            v = v.replace('"', "'")
        else:
            v = utils.xhtml_escape(v)

        return v

    def _flatten(self, iterable):
        if not isinstance(iterable, (list, tuple)):
            yield self._get_html_value(iterable)
        else:
            for value in iterable:
                if isinstance(value, (list, tuple)):
                    for sub_value in self._flatten(value):
                        if sub_value:
                            yield self._get_html_value(sub_value)
                elif value:
                    yield self._get_html_value(value)

    def get_inline_content(self):
        inline_content = self.content

        if self.evaluate:
            inline_content = self.node.parser.target.eval(inline_content)

        return inline_content

    def render(self, content='', indentation=0):
        buf = []

        attributes = [self.tag, self.get_attributes()]

        if self.autoclose:
            attributes.append('/')

        buf.append(utils.indent('<%s>' % ' '.join(filter(bool, attributes)), indentation))

        if not self.autoclose:
            content_buf = []

            if self.content:
                content_buf.append(self.get_inline_content())

            if content:
                content_buf.append(_NEWLINE)
                content_buf.append(content)
                content_buf.append(_NEWLINE)
            else:
                indentation = 0

            if self.innerstrip:
                buf.append(''.join(content_buf).strip())
                indentation = 0
            else:
                buf.extend(content_buf)

            buf.append(utils.indent('</%s>' % self.tag, indentation))

        return ''.join(map(str, buf))