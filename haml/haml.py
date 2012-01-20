from .node import Node
from .target import Default
import hashlib

_CACHE = {}

class HAML(object):
    def __init__(self, haml, target=Default):
        self.sha1 = hashlib.sha1(haml).hexdigest()
        self.node = Node(self, '', haml)
        self.target = target()

    def __str__(self):
        return self.to_html()

    def __unicode__(self):
        return self.to_html()

    def to_html(self):
        if self.sha1 not in _CACHE:
            _CACHE[self.sha1] = self.node.to_html()

        return _CACHE[self.sha1]
