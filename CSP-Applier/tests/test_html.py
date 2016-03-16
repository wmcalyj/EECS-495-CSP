#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import unittest
import os
import glob
import shutil
from hashlib import sha1
from bs4 import BeautifulSoup
from csp_applier import html

class TestHTMLParser(unittest.TestCase):
    def setUp(self):
        soup = BeautifulSoup(open("resources/test.html"))
        self.parser = html.HTMLParser(soup)

    def test_extract_js(self):
        external, inline, attr = self.parser.scripts
        self.assertEqual(4, len(external))
        self.assertEqual(6, len(inline))
        self.assertEqual(7, len(attr))

        for event, tag, uuid in attr:
            if event == 'onclick' and tag[event] == 'myfunction1()':
                self.assertEqual('button1', tag['id'])
            if event == 'onclick' and tag[event] == 'myfunction2()':
                self.assertTrue('button2' in tag['class'])
            if event == 'onmouseover' and tag[event] == 'myfunction4()':
                self.assertTrue('button2' in tag['class'])
            if event == 'onmouseover' and tag[event] == 'myfunction3()':
                self.assertEqual('button3', tag['id'])
            if event == 'onclick' and tag[event] == 'myfunction3()':
                self.assertEqual('button3', tag['id'])
            if event == 'onsubmit' and tag[event] == 'myfunction4()':
                self.assertEqual('get', tag['method'])
            if event == 'onsubmit' and tag[event] == 'myfunction5()':
                self.assertEqual('form1', tag['id'])

    def test_extract_css(self):
        external, inline, attr = self.parser.styles
        self.assertEqual(1, len(inline))
        self.assertEqual(3, len(attr))

class TestHTMLGenerator(unittest.TestCase):
    def setUp(self):
        parser = html.HTMLParser(BeautifulSoup(open("resources/test.html")))

        external_js, inline_js, attr_js = parser.scripts
        external_css, inline_css, attr_css = parser.styles
        filter_list = [external_js[2][2], inline_js[1][1], inline_js[2][1], attr_js[3][2], attr_js[5][2],
                       inline_css[0][1], attr_css[1][1]]

        file_name = sha1("http://www.test.com").hexdigest()
        root_dir = "/tmp"
        root_http_path = "http://127.0.0.1"
        self.generator = html.HTMLGenerator(parser, filter_list, file_name, root_dir, root_http_path)

    def tearDown(self):
        shutil.rmtree(self.generator.directory)

    def test_if_dir_created(self):
        self.assertTrue(os.path.exists(self.generator.directory))

    def test_generate_inline_js(self):
        external, inline, attr = self.generator.html_parser.scripts
        self.generator.generate_inline_js(inline)
        self.assertEquals(4, len(glob.glob1(self.generator.directory, "*_inline.js")))

    def test_generate_attr_js(self):
        external, inline, attr = self.generator.html_parser.scripts
        self.generator.generate_attr_js(attr)
        js_filename = self.generator.directory + self.generator.file_name + "_events.js"
        self.assertTrue(os.path.isfile(js_filename))

        count = 0
        f = open(js_filename, 'r')
        for line in f.readlines():
            if line.startswith("// CSP-Applier"):
                count += 1
        f.close()
        self.assertEqual(5, count)

    def test_write_css(self):
        self.generator.write_css()
        css_filename = self.generator.directory + self.generator.file_name + ".css"
        self.assertTrue(os.path.isfile(css_filename))

        count = 0
        f = open(css_filename, 'r')
        for line in f.readlines():
            if line.startswith("/* CSP-Applier"):
                count += 1
        f.close()
        self.assertEqual(2, count)

    def test_generate_html(self):
        parser = self.generator.html_parser
        self.generator.rewrite_html()

        events = ["onclick", "onsubmit", "onmouseover"]
        count_js_ext = 0
        count_js_inline = 0
        count_js_attr = 0
        for tag in parser.soup.find_all('script'):
            if tag.has_attr('src'):
                count_js_ext += 1
            else:
                count_js_inline += 1
        for listener in events:
            for tag in parser.soup.find_all(True):
                if tag.has_attr(listener):
                    count_js_attr += 1
        # 3 orig ext_js + 4 orig inline + 1 orig attr
        self.assertEqual(8, count_js_ext)
        self.assertEqual(0, count_js_inline)
        self.assertEqual(0, count_js_attr)

if __name__ == "__main__":
    unittest.main()
