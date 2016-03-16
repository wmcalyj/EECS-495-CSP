#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from hashlib import sha1

class Template:
    def __init__(self, entry=None):
        self.template = entry if entry else {}

    def compare(self, html):
        """
        Compares the given HTML with the template and output the blacklist

        :param html: A HTMLParser object
        :return: A list of uuid string
        """
        return self.compare_js(html.scripts) + self.compare_css(html.styles)

    def compare_js(self, scripts):
        """
        Compares the JS of the given HTML with template and output the blacklist of JS

        :param scripts: A tuple of external JS, inline JS and JS as attribute of a tag
        :return: A list of uuid string
        """
        external_js, inline_js, attr_js = scripts
        return self.compare_external_js(external_js) + \
            self.compare_inline_js(inline_js) + \
            self.compare_attr_js(attr_js)

    def compare_css(self, styles):
        """
        Compares the CSS of the given HTML with template and output the blacklist of CSS

        :param styles: A tuple of external CSS, inline CSS and CSS as attribute of a tag
        :return: A list of uuid string
        """
        external_css, inline_css, attr_css = styles
        return self.compare_external_css(external_css) + \
            self.compare_inline_css(inline_css) + \
            self.compare_attr_css(attr_css)

    def compare_external_js(self, external_js):
        filter_list = []
        for src, tag, uuid in external_js:
            if sha1(src).hexdigest() not in self.template['js'].keys():
                filter_list.append(uuid)
        return filter_list

    def compare_inline_js(self, inline_js):
        filter_list = []
        for tag, uuid in inline_js:
            if sha1(unicode(tag.string)).hexdigest() not in self.template['js'].keys():
                filter_list.append(uuid)
        return filter_list

    def compare_attr_js(self, attr_js):
        filter_list = []
        for event, tag, uuid in attr_js:
            if sha1(unicode(tag[event])).hexdigest() not in self.template['js'].keys():
                filter_list.append(uuid)
        return filter_list

    def compare_external_css(self, external_css):
        filter_list = []
        for href, tag, uuid in external_css:
            if sha1(href).hexdigest() not in self.template['css'].keys():
                filter_list.append(uuid)
        return filter_list

    def compare_inline_css(self, inline_css):
        filter_list = []
        for tag, uuid in inline_css:
            if sha1(unicode(tag.string)).hexdigest() not in self.template['css'].keys():
                filter_list.append(uuid)
        return filter_list

    def compare_attr_css(self, attr_css):
        filter_list = []
        for tag, uuid in attr_css:
            if sha1(unicode(tag["style"])).hexdigest() not in self.template['css'].keys():
                filter_list.append(uuid)
        return filter_list

    # Get the info for CSP
    def get_csp_src(self):
        return self.template["csp-sources"]
