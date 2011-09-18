from .node import Node

class HAML(object):
    def __init__(self, haml):
        self.haml = Node('', haml)

    def __str__(self):
        return self.to_html()

    def __unicode__(self):
        return self.to_html()

    def to_html(self):
        return self.haml.to_html()
        