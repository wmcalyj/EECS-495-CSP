#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from hashlib import sha1

class NaiveTemplate:
    """
    Create a naive template based on the sha1sum of the JS/CSS
    """

    def __init__(self, html_parser):
        self.js_dict = {}
        self.css_dict = {}
        self.html_parser = html_parser

    def build_js(self):
        external_js, inline_js, attr_js = self.html_parser.scripts

        for src, tag, uuid in external_js:
            hash_str = sha1(src).hexdigest()
            self.js_dict.setdefault(hash_str, []).append(self.tag_to_dict(tag))

        for tag, uuid in inline_js:
            hash_str = sha1(unicode(tag.string)).hexdigest()
            self.js_dict.setdefault(hash_str, []).append(self.tag_to_dict(tag))

        for event, tag, uuid in attr_js:
            hash_str = sha1(unicode(tag[event])).hexdigest()
            self.js_dict.setdefault(hash_str, []).append(self.tag_to_dict(tag, event=event))

    def build_css(self):
        external_css, inline_css, attr_css = self.html_parser.styles

        for href, tag, uuid in external_css:
            hash_str = sha1(href).hexdigest()
            self.css_dict.setdefault(hash_str, []).append(self.tag_to_dict(tag))

        for tag, uuid in inline_css:
            hash_str = sha1(unicode(tag.string)).hexdigest()
            self.css_dict.setdefault(hash_str, []).append(self.tag_to_dict(tag))

        for tag, uuid in attr_css:
            hash_str = sha1(unicode(tag["style"])).hexdigest()
            self.css_dict.setdefault(hash_str, []).append(self.tag_to_dict(tag))

    def generate_template(self):
        self.build_js()
        self.build_css()
        return {"js": self.js_dict, "css": self.css_dict}

    def tag_to_dict(self, tag, event=None):
        extra = {"tag": tag.name, "path": self.find_path(tag, [])}

        if event:
            extra["csp_event"] = event

        return self.merge_dict(tag.attrs, extra)

    def find_path(self, tag, tag_path):
        parent = tag.parent
        if parent is None:
            return tag_path
        else:
            info = parent.attrs.copy()
            info["tag"] = parent.name
            tag_path.append(info)

        return self.find_path(parent, tag_path)

    @staticmethod
    def merge_dict(x, y):
        z = x.copy()
        z.update(y)
        return z

