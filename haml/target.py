from .node import CodeNode

class Default(object):
    CONTROL = '%s'
    EVAL = '%s'
    RULES = {}

    def block(self, node, keyword, expression):
        # Open

        if keyword in self.RULES and 'open' in self.RULES[keyword]:
            open = self.RULES[keyword]['open']
        else:
            open = '%(keyword)s %(expression)s'

        open = self.CONTROL % (open % {
            'keyword': keyword,
            'expression': expression,
        })

        # Close

        close = ''

        sibling = node.get_sibling(1)

        try:
            continuation = self.RULES[keyword].get('continuation')

            if not (isinstance(sibling, CodeNode) and continuation and sibling.keyword in continuation):
                close = self.CONTROL % self.RULES[keyword]['close']
        except KeyError:
            pass

        return open, close

    def eval(self, input):
        return self.EVAL % input

class Tornado(Default):
    CONTROL = '{%% %s %%}'
    EVAL = '{{ %s }}'
    RULES = {
        'for': {
            'close': 'end',
        },
        'if' : {
            'close': 'end',
            'continuation': [
                'elif',
                'else',
            ],
        },
        'elif': {
            'continuation': [
                'elif',
                'else',
            ],
            'close': 'end',
        },
        'else': {
            'close': 'end',
        },
        'block': {
            'close': 'end',
        },
    }


class Underscore(Default):
    CONTROL = '<%% %s %%>'
    EVAL = '<%%= %s %%>'
    RULES = {
        'for': {
            'open': 'for (%(expression)s) {',
            'close': '}',
            },
        'if' : {
            'open': 'if (%(expression)s) {',
            'close': '}',
            'continuation': [
                'elif',
                'else',
            ],
        },
        'elif': {
            'continuation': [
                'elif',
                'else',
            ],
            'open': '} else if (%(expression)s) {',
            'close': '}',
        },
        'else': {
            'open': '} else {',
            'close': '}',
        },
        'set': {
            'open': 'var %(keyword)s %(expression)s;'
        }
    }

    def __init__(self):
        self._ref = 0

    def block(self, node, keyword, expression):
        if keyword == 'for':
            var, enumerable = expression.split(' in ')

            self._ref += 1

            FOR = (
                'for (var _i%(ref)d=0,_length%(ref)d=%(enumerable)s.length;'
                '_i%(ref)d<_length%(ref)d;'
                '_i%(ref)d++){'
                'var %(var)s=%(enumerable)s[_i%(ref)d];'
            )

            return self.CONTROL % (FOR % {'ref': self._ref,'enumerable': enumerable, 'var': var}), self.CONTROL % '}'
        else:
            return super(Underscore, self).block(node, keyword, expression)