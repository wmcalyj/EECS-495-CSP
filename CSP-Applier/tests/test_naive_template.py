#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import unittest
from hashlib import sha1

from bs4 import BeautifulSoup

from csp_applier import naive_template, html


class TestNaiveTemplate(unittest.TestCase):
    def setUp(self):
        html_parser = html.HTMLParser(BeautifulSoup(open("resources/test.html")))
        self.template = naive_template.NaiveTemplate(html_parser)

    def tearDown(self):
        return

    def test_find_path(self):
        tag = self.template.html_parser.soup.find(id="button1")
        path = self.template.find_path(tag, [])
        self.assertEqual("div", path[0]["tag"])
        self.assertEqual("test-div", path[0]["id"])
        self.assertEqual("body", path[1]["tag"])
        self.assertEqual("html", path[2]["tag"])

    def test_tag_to_dict(self):
        tag = self.template.html_parser.soup.find(id="button1")
        json_tag = self.template.tag_to_dict(tag, event="onclick")
        self.assertEqual("button", json_tag["tag"])
        self.assertEqual("button1", json_tag["id"])
        self.assertEqual(["button1"], json_tag["class"])
        self.assertEqual("onclick", json_tag["csp_event"])

    def test_build_js(self):
        self.template.build_js()
        js_dict = self.template.js_dict

        # There are 17 js in total, 2 pairs of them have duplicated content
        self.assertEqual(15, len(js_dict.keys()))

        # There are two events with the same JS content in different tags
        hash_key = sha1("myfunction4()").hexdigest()
        self.assertEqual(2, len(js_dict[hash_key]))

        # There are two events with the same JS content in the same tag
        hash_key = sha1("myfunction3()").hexdigest()
        self.assertEqual(2, len(js_dict[hash_key]))
        self.assertEqual(js_dict[hash_key][0]["id"], js_dict[hash_key][1]["id"])

    def test_build_css(self):
        self.template.build_css()
        css_dict = self.template.css_dict

        # There are 5 in total, two of them are duplicated
        self.assertEqual(4, len(css_dict.keys()))

        hash_key = sha1("color:sienna;margin-left:20px;").hexdigest()
        self.assertEqual(2, len(css_dict[hash_key]))

if __name__ == "__main__":
    unittest.main()
