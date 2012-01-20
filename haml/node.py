import re
from .constants import OPERATORS, INDENT
from .element import HTMLElement
from . import utils

class StripOuter(Exception):
    def __init__(self, html, *args, **kwargs):
        super(StripOuter, self).__init__(*args, **kwargs)
        self.html = html

class Node(object):
    PARSE = True

    @staticmethod
    def create(parser, haml, nested_haml='', parent=None, indentation=-1):
        haml = haml.strip()

        NODES = [
            (HAMLComment, '-#'),
            (HTMLCommentNode, '/'),
            (HTMLNode, ('#', '.', '%')),
            (CodeNode, '-'),
            (EvalNode, ('=', '>=')),
            (DoctypeNode, '!!!'),
            (RawNode, ('\\', '>')),

            # Filters
            (PlainFilterNode, ':plain'),
            (JavaScriptFilterNode, ':javascript'),
            (CssFilterNode, ':css'),
            (CdataFilterNode, ':cdata'),
            (EscapedFilterNode, ':escaped'),
        ]

        for cls, operators in NODES:
            if not isinstance(operators, tuple):
                operators = (operators,)

            for operator in operators:
                if haml.startswith(operator):
                    return cls(parser, haml, nested_haml, parent, indentation=indentation)

        return RawNode(parser, haml, nested_haml, parent, indentation=indentation)

    def __init__(self, parser, haml, nested_haml='', parent=None, indentation=-1):
        self.parser = parser
        self.haml = haml
        self.nested_haml = nested_haml
        self.parent = parent
        self.siblings = {
            'left': [],
            'right': []
        }
        self.children = []
        self.indentation = indentation

        if not self.PARSE:
            return

        if isinstance(nested_haml, list):
            lines = nested_haml
        else:
            lines = [line for line in nested_haml.split('\n') if line]

        while lines:
            line = lines.pop(0)

            line_indentation = utils.indentation(line)

            MULTILINE = OPERATORS['multiline']

            if line.rstrip().endswith(MULTILINE):
                m_lines = [line.rstrip()]

                while True:
                    try:
                        if lines[0].endswith(MULTILINE):
                            m_lines.append(lines.pop(0).rstrip())
                        else:
                            break
                    except IndexError:
                        break

                line = self._indent(' '.join(line.rstrip(MULTILINE).strip() for line in m_lines), line_indentation)

            nested_lines = []

            while True:
                if not lines:
                    break

                try:
                    if utils.indentation(lines[0]) <= line_indentation:
                        break
                    else:
                        nested_lines.append(lines.pop(0))
                except IndexError:
                    break

            node = Node.create(self.parser, line, nested_lines, parent=self, indentation=self.indentation + 1)

            for child in self.children:
                node.add_sibling('left', child)
                child.add_sibling('right', node)

            self.children.append(node)

    def add_sibling(self, location, sibling):
        location = location.lower()
        assert location in ('left', 'right')
        self.siblings[location].append(sibling)

    def get_sibling(self, n):
        if n < 0:
            siblings = self.siblings['left']
        elif n > 0:
            siblings = self.siblings['right']
        else:
            return None

        if not len(siblings):
            return None

        n = abs(n) - 1

        if n > len(siblings):
            return None

        return siblings[n]

    def _indent(self, line, indentation=None):
        return utils.indent(line, indentation or self.indentation)

    def render_children(self):
        rendered_children = []

        outerstrip = False
        length = len(self.children)

        for i, child in enumerate(self.children):
            lstrip = outerstrip

            try:
                html = child.to_html()
                outerstrip = False
            except StripOuter as so:
                html = so.html
                outerstrip = True

                if rendered_children:
                    rendered_children[-1] = rendered_children[-1].rstrip()

            if lstrip:
                html = html.lstrip()

            if html is not None:
                if outerstrip:
                    rendered_children.append(html.strip())
                else:
                    if i < length - 1:
                        html += '\n'

                    rendered_children.append(html)

        return ''.join(rendered_children)

    def to_html(self):
        html = self.render_children()

        if html:
            html = re.sub(r'#\{(.*?)\}', self.parser.target.eval('\\1'), html + '\n')

        return html

class RawNode(Node):
    def to_html(self):
        content = self.haml

        if content.startswith(OPERATORS['outerstrip']):
            raise StripOuter(self._indent(content[1:]))

        if content.startswith(OPERATORS['escape']):
            content = content[1:]

        return self._indent(content)

class DoctypeNode(Node):
    DOCTYPES = {
        'Strict': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">',
        'Frameset': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">',
        '5': '<!DOCTYPE html>',
        '1.1': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">',
        'Mobile': '<!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.2//EN" "http://www.openmobilealliance.org/tech/DTD/xhtml-mobile12.dtd">',
        'RDFa': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML+RDFa 1.0//EN" "http://www.w3.org/MarkUp/DTD/xhtml-rdfa-1.dtd">',
        'XML': '<?xml version="1.0" encoding="utf-8" ?>',
    }

    def to_html(self):
        doctype = self.haml.lstrip(OPERATORS['doctype']).strip()
        return self.DOCTYPES.get(doctype, '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')

class HTMLNode(Node):
    def to_html(self):
        indentation = self.indentation

        element =  HTMLElement(self)
        html = element.render(self.render_children(), indentation=indentation)

        if element.outerstrip:
            raise StripOuter(html)
        else:
            return html

class HTMLCommentNode(Node):
    def to_html(self):
        conditionals = re.findall(r'^/\[(.*?)\]', self.haml)

        if conditionals:
            start = '<!--[%s]>' % conditionals[0]
            end = '<!endif-->'
        else:
            start = '<!--'
            end = '-->'

        rendered_children = self.render_children()

        if rendered_children:
            return '\n'.join([self._indent(start), rendered_children, self._indent(end)])

        return self._indent(' '.join([start, self.haml.lstrip(OPERATORS['html-comment']).lstrip(), end]))

class HAMLComment(Node):
    def to_html(self):
        return None

class EvalNode(Node):
    def to_html(self):
        content = self._indent(self.parser.target.eval(self.haml.lstrip(OPERATORS['outerstrip']).lstrip(OPERATORS['evaluate']).strip()))

        if self.haml.startswith(OPERATORS['outerstrip']):
            raise StripOuter(content)

        return content

class CodeNode(Node):
    def __init__(self, *args, **kwargs):
        Node.__init__(self, *args, **kwargs)

        parts = self.haml.lstrip(OPERATORS['code']).strip().split(' ', 1)

        self.keyword = parts[0]
        self.expression = ''

        if len(parts) > 1:
            self.expression = parts[1]

    def to_html(self):
        open, close = self.parser.target.block(self, self.keyword, self.expression)

        return '\n'.join(filter(bool, (self._indent(open), self.render_children(), self._indent(close))))

class PlainFilterNode(Node):
    PARSE = False

    def to_html(self):
        return '\n'.join([line[INDENT:] for line in self.nested_haml])

class EscapedFilterNode(PlainFilterNode):
    PARSE = False

    def to_html(self):
        return utils.xhtml_escape(PlainFilterNode.to_html(self))

class CdataFilterNode(Node):
    PARSE = False

    def to_html(self):
        buf = [self._indent('//<![CDATA[', self.indentation)]

        for line in self.nested_haml:
            buf.append(line[INDENT:])

        buf.append(self._indent('//]]>', self.indentation))

        return '\n'.join(buf)

class JavaScriptFilterNode(Node):
    PARSE = False

    def to_html(self):
        buf = [self._indent('<script type="text/javascript">'), self._indent('//<![CDATA[', self.indentation + 1)]

        for line in self.nested_haml:
            buf.append(line[INDENT:])

        buf.append(self._indent('//]]>', self.indentation + 1))
        buf.append(self._indent('</script>'))

        return '\n'.join(buf)

class CssFilterNode(Node):
    PARSE = False

    def to_html(self):
        buf = [self._indent('<style type="text/css">'), self._indent('//<![CDATA[', self.indentation + 1)]

        for line in self.nested_haml:
            buf.append(line[INDENT:])

        buf.append(self._indent('//]]>', self.indentation + 1))
        buf.append(self._indent('</style>'))

        return '\n'.join(buf)