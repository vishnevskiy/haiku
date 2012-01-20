from .node import Node
from .target import Default

class HAML(object):
    def __init__(self, haml, target=Default):
        self.node = Node(self, '', haml)
        self.target = target()

    def __str__(self):
        return self.to_html()

    def __unicode__(self):
        return self.to_html()

    def to_html(self):
        return self.node.to_html()
        