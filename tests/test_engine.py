import unittest
import haml

class EngineTest(unittest.TestCase):
    def _render(self, v):
        return haml.HAML(v).to_html()

    def test_empty_render(self):
        self.assertEqual('', self._render(''))

    def test_flexible_tabulation(self):
        self.assertEqual("<p>\n  foo\n</p>\n<q>\n  bar\n  <a>\n    baz\n  </a>\n</q>\n",  self._render("%p\n foo\n%q\n bar\n %a\n  baz"))
        self.assertEqual("<p>\n  foo\n</p>\n<q>\n  bar\n  <a>\n    baz\n  </a>\n</q>\n", self._render("%p\n\tfoo\n%q\n\tbar\n\t%a\n\t\tbaz"))
        self.assertEqual("<p>\n      \t \t bar\n   baz\n</p>\n", self._render("%p\n  :plain\n        \t \t bar\n     baz"))

    def test_attributes_should_render_correctly(self):
        self.assertEqual('<div class="atlantis" style="ugly"></div>', self._render(".atlantis{'style':'ugly'}").strip())

    def test_css_id_as_attribute_should_be_appended_with_underscore(self):
        self.assertEqual('<div id="my_id_1"></div>', self._render("#my_id{'id': '1'}").strip())
        self.assertEqual('<div id="my_id_1"></div>', self._render("#my_id{'id': 1}").strip())

    def test_code_should_work_inside_attributes(self):
        self.assertEqual('<p class="3">foo</p>', self._render("%p{'class': 1+2} foo").strip())

    def test_class_attr_with_list(self):
        self.assertEqual('<p class="a b">foo</p>\n', self._render("%p{'class': ['a', 'b']} foo")) # basic
        self.assertEqual('<p class="a b css">foo</p>\n', self._render("%p.css{'class': ['a', 'b']} foo")) # merge with css
        self.assertEqual('<p class="b css">foo</p>\n', self._render("%p.css{'class': ['css', 'b']} foo")) # merge uniquely
        self.assertEqual('<p class="a b c d">foo</p>\n', self._render("%p{'class': [['a', 'b'], ['c', 'd']]} foo")) # flatten
        self.assertEqual('<p>foo</p>\n', self._render("%p{'class': [None, False]} foo")) # strip falsey
        self.assertEqual('<p class="a">foo</p>\n', self._render("%p{'class': 'a'} foo")) # single stringify
        self.assertEqual('<p>foo</p>\n', self._render("%p{'class': False} foo")) # single falsey

    def test_id_attr_with_list(self):
        self.assertEqual('<p id="a_b">foo</p>\n', self._render("%p{'id': ['a', 'b']} foo")) # basic
        self.assertEqual('<p id="css_a_b">foo</p>\n', self._render("%p#css{'id': ['a', 'b']} foo")) # merge with css
        self.assertEqual('<p id="a_b_c_d">foo</p>\n', self._render("%p{'id': [['a', 'b'], ['c', 'd']]} foo")) # flatten
        self.assertEqual('<p id="a_b">foo</p>\n', self._render("%p{'id': ['a', 'b'] } foo")) # stringify
        self.assertEqual('<p>foo</p>\n', self._render("%p{'id': [None, False] } foo")) # strip falsey
        self.assertEqual('<p id="a">foo</p>\n', self._render("%p{'id': 'a'} foo")) # single stringify
        self.assertEqual('<p>foo</p>\n', self._render("%p{'id': False} foo")) # single falsey

    def test_colon_in_class_attr(self):
        self.assertEqual('<p class="foo:bar" />\n', self._render("%p.foo:bar/"))

    def test_colon_in_id_attr(self):
        self.assertEqual('<p id="foo:bar" />\n', self._render("%p#foo:bar/"))

    def test_dynamic_attributes_with_no_content(self):
        self.assertEqual("""<p>
  <a href="http://haml-lang.com"></a>
</p>
""", self._render("""
%p
  %a{'href': 'http://' + 'haml-lang.com'}
"""))

    def test_attributes_with_to_s(self):
        self.assertEqual("""<p id="foo_2"></p>
<p class="2 foo"></p>
<p blaz="2"></p>
<p 2="2"></p>
""", self._render("""%p#foo{'id': 1+1}
%p.foo{'class': 1+1}
%p{'blaz': 1+1}
%p{(1+1): 1+1}
"""))

    def test_none_should_render_empty_tag(self):
        self.assertEqual('<div class="no_attributes"></div>', self._render(".no_attributes{None: None}").strip())

    def test_strings_should_get_stripped_inside_tags(self):
        self.assertEqual('<div class="stripped">This should have no spaces in front of it</div>',
                   self._render(".stripped    This should have no spaces in front of it").strip())

    def test_one_liner_should_be_one_line(self):
        self.assertEqual("<p>Hello</p>", self._render('%p Hello').strip())

    # TODO: convert the remaining tests from Ruby version
        
if __name__ == '__main__':
    unittest.main()
        