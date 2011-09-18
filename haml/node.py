from .constants import OPERATORS
from .element import HTMLElement
from . import utils

class Node(object):
    @staticmethod
    def create(haml, nested_haml='', parent=None):
        indentation = utils.indentation(haml)
        haml = haml.strip()

        NODES = {
            '%': HTMLNode,
            '#': HTMLNode,
            '.': HTMLNode,
            '-': CodeNode,
            '=': EvalNode,
            '!!!': DoctypeNode,
            '\\': PlainNode,
        }

        for operator, cls in NODES.items():
            if haml.startswith(operator):
                return cls(haml, nested_haml, parent, indentation=indentation)

        return PlainNode(haml, nested_haml, parent, indentation=indentation)

    def __init__(self, haml, nested_haml='', parent=None, indentation=0):
        self.haml = haml
        self.parent = parent
        self.siblings = {'left': [], 'right': []}
        self.children = []
        self.indentation = indentation

        if isinstance(nested_haml, list):
            lines = nested_haml
        else:
            lines = [line.rstrip() for line in nested_haml.split('\n') if line]

        while lines:
            line = lines.pop(0)
            
            line_indentation = utils.indentation(line)

            MULTILINE = OPERATORS['multiline']

            if line.endswith(MULTILINE):
                m_lines = [line]

                while True:
                    try:
                        if lines[0].endswith(MULTILINE):
                            m_lines.append(lines.pop(0))
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

            node = Node.create(line, nested_lines, parent=self)

            if not node:
                continue

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

        for children in self.children:
            rendered_children.append(children.to_html())

        return '\n'.join(rendered_children)

    def to_html(self):
        return self.render_children()

class PlainNode(Node):
    def to_html(self):
        content = self.haml

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

#        current = self.parent
#
#        while current:
#            if isinstance(current, CodeNode):
#                indentation = current.indentation
#
#            current = current.parent

        return HTMLElement(self.haml).render(self.render_children(), indentation=indentation)

class EvalNode(Node):
    def to_html(self):
        return self._indent('{{ %s }}' % (self.haml.lstrip(OPERATORS['evaluate']).strip()))

class CodeNode(Node):
    LOGIC = {
        'for': {
            'close': 'end',
        },
        'if' : {
            'close': 'end',
            'continuation': ['elif', 'else'],
        },
        'elif': {
            'continuation': ['else'],
            'close': 'end',
            },
        'else': {
            'close': 'end',
            },
        'block': {
            'close': 'end',
        },
    }

    def __init__(self, *args, **kwargs):
        Node.__init__(self, *args, **kwargs)
        self._op = self.haml.strip().split(' ')[1]

    def to_html(self):
        buf = [self._indent('{% ' + self.haml.lstrip(OPERATORS['code']).strip() + ' %}'), self.render_children()]

        if self._op in self.LOGIC:
            sibling = self.get_sibling(1)

            try:
                continuation = self.LOGIC[self._op].get('continuation')

                if  not (sibling and isinstance(sibling, CodeNode)) or not continuation or sibling._op in continuation:
                    buf.append(self._indent('{% ' + self.LOGIC[self._op]['close'] + ' %}'))
            except KeyError:
                pass

        return '\n'.join(filter(bool, buf))
