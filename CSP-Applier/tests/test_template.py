#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import unittest
from hashlib import sha1
from bs4 import BeautifulSoup
from csp_applier import naive_template, html, template, mongo_driver

class TestTemplate(unittest.TestCase):
    def setUp(self):
        parser = html.HTMLParser(BeautifulSoup(open("resources/test.html")))
        self.template = template.Template(naive_template.NaiveTemplate(parser).generate_template())

        self.changes = [
            sha1("myfunction_evil()").hexdigest(),
            sha1("evil_yeah()").hexdigest(),
            sha1("color:red;margin-left:20px;").hexdigest()
        ]

    def test_compare(self):
        evil_parser = html.HTMLParser(BeautifulSoup(open("resources/test_evil.html")))
        filter_list = self.template.compare(evil_parser)
        self.assertEqual(3, len(filter_list))

        external, inline, attr = evil_parser.scripts
        for event, tag, uuid in attr:
            if uuid in filter_list:
                self.assertTrue(sha1(unicode(tag[event])).hexdigest() in self.changes)

        external, inline, attr = evil_parser.styles
        for tag, uuid in attr:
            if uuid in filter_list:
                self.assertTrue(sha1(unicode(tag["style"])).hexdigest() in self.changes)

class TestMongoDriver(unittest.TestCase):
    def setUp(self):
        self.mongo = mongo_driver.MongoDriver()
        parser = html.HTMLParser(BeautifulSoup(open("resources/test.html")))
        self.template = naive_template.NaiveTemplate(parser).generate_template()
        self.url = "http://www.test.com"

    def tearDown(self):
        self.mongo.collection.remove({"key": sha1(self.url).hexdigest()})

    def test_operations(self):
        """
        Here only insert/query operations are tested.

        :return: None
        """
        self.mongo.insert({"key": sha1(self.url).hexdigest(),
                           "pattern": self.template})
        result = self.mongo.query(sha1(self.url).hexdigest())
        self.assertTrue("pattern" in result.keys())

if __name__ == "__main__":
    unittest.main()
