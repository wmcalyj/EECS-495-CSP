import scrapy
import re
import os, sys
from scrapy.selector import HtmlXPathSelector
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
import urlparse
import logging
import re
import urllib2
import json
import base64
import tldextract

from scrapy.exceptions import CloseSpider

#logging.basicConfig(filename='spider.log',level=logging.INFO)

count = 0
FOLDER = "urls"
HOST = "lotus.cs.northwestern.edu:4040"

global rendered_urls
rendered_urls =  set()

#logger = logging.getLogger('DOMCluster')
#hdlr = logging.FileHandler('./cluster.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#hdlr.setFormatter(formatter)
#consoleHandler = logging.StreamHandler()
#consoleHandler.setFormatter(formatter)
#logger.addHandler(hdlr) 
#logger.addHandler(consoleHandler)
#logger.setLevel(logging.INFO)

# Command should look like this:
# scrapy runspider my_spider.py -a domains=bbc.com -a urls=http://www.bbc.com

def storeUrls(url, self):
    try:
            host = "http://" + HOST + "/api/web-contents/rendered-urls-store"
            req = urllib2.Request(host)
            req.add_header('Content-Type', 'application/json')

            data = { 
                'url' : base64.b64encode(url.strip()),
                'cookies' : self.cookies,
                'domain' : [base64.b64encode(x.strip()) for x in self.domains],
                'rendered' : False}

            response = urllib2.urlopen(req, json.dumps(data))
            rs = json.loads(response.read())
            
            if rs['success']:
                logging.info("[SUCCEED] successfully store url %s", url)
                return True
            else:
                logging.warning("[FAILURE] Failed to store url %s", url)
                print "Failed to store url " % url
                return False

    except Exception as e:
            print >> sys.stderr, "Exception in storeUrls: " + str(e)
            return False


class MySpider(scrapy.Spider):

    name = "mySpider"

    def __init__ (self, method=None, domains=None, urls=None, filename=None, maxurls=None, cookies=None, userAgent=None, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        domain_url_dict = {}
        
        _domains = [x.strip() for x in domains.split("|")]
        self.domains = list()
        for x in _domains:
            result = tldextract.extract(x)
            self.domains.append(result.domain + "." + result.suffix)
            # ExtractResult(subdomain='forums.news', domain='cnn', suffix='com')

        _urls = [x.strip() for x in urls.split("|")]
        domain_url_dict[0] = (_domains, _urls)
        
        self.maxurls = int(maxurls)
        # self.userAgent = str(userAgent)
        #self.userAgent = [base64.b64encode(x.strip() for x in userAgent.split("|")]
        # self.cookies = str(cookies)
        self.cookies = ""
        if cookies != None: 
            # Use space to sperate different cookies
            self.cookies = [base64.b64encode(x.strip()) for x in cookies.split(" ")]

        # For python 3, please use list(domain_url_dict.values())
        for domain_url_tuple in domain_url_dict.values():
            self.allowed_domains = domain_url_tuple[0]
            self.start_urls = domain_url_tuple[1]

        self.outputfile = filename

    SPIDER_MIDDLEWARES = {
            'scrapy.spidermiddlewares.referer.RefererMiddleware': None,
    }


    if not os.path.exists(FOLDER):
            os.mkdir(FOLDER, 0755)
    
    global c
    c = 1
    

        # all domains and urls found, create a folder that contains all of the urls
        #logging.info("start urls: %s", all_urls)
        #logging.info("allowed_domains: %s", all_domains)

        #for domain in all_domains:

    def parse(self, response):

            max_url = int(self.maxurls)

            # set a list of regex to filter unwanted urls
            # Just filter jpg, doc, ppt & pdf. To filter more type
            # please add it to regex_unwanted as a lsit
            regex_unwanted = ['^.*\.(jpg|JPG|JPEG|jpeg|pdf|doc|docx|ppt)$']
            wantedExtracted = tldextract.extract(self.domains[0])
            wantedDomain = wantedExtracted.domain + "." + wantedExtracted.suffix
            
            # Loop all urls
            current_url = response.url.strip()
            if not current_url in rendered_urls:
                    # We will add the current url to rendered as well, although this might
                    # not be the url that we record
                    rendered_urls
                    rendered_urls.add(current_url)

            filename = self.allowed_domains[0]
            if not self.outputfile is None:
                filename = self.outputfile

            filePath = FOLDER + "/" + filename + ".txt"
            logging.debug("current url: %s", current_url)
            for url in response.xpath('//a/@href').extract():
                    # url might be relative path, complete it with full path
                    full_url = urlparse.urljoin(current_url, url).strip()
                    # If the last char of full_url ends up with /, delete it
                    if full_url[-1] == '/':
                            full_url = full_url[:-1]

                    unwanted = False
                    for pattern in regex_unwanted:
                            if not re.match(pattern, full_url) == None:
                                    unwanted = True
                                    break
                    # Here, we only check against domain, not the suffix
                    # If we want to check the suffix as well, it's doable
                    # By doing this, we can also eliminate invalid urls (partially)
                    extracted = tldextract.extract(full_url)
                    resultDomain = extracted.domain + "." + extracted.suffix
                    if resultDomain != wantedDomain:
                        unwanted = True

                    if not full_url in rendered_urls and (not unwanted):
                            # Update rendered urls and keep tracking of them
                            rendered_urls.add(full_url)
                            global count
                            with open(filePath, 'a+') as fw:
                                    fw.write(full_url + "\n")
                            storeUrls(full_url, self)
                            logging.debug("new url found: %d - %s for domain - %s", count, full_url, resultDomain)
                            count += + 1
                            yield scrapy.Request(full_url, callback=self.parse)
                    if count >= max_url:
                           raise CloseSpider('Max urls %d reached' % max_url)
                    if len(rendered_urls) > 5000:
                        # This is to clear the rendered urls in memory for efficiency purpose.
                        # Unique url is promised while inserting to database, so no worries :)
                        del rendered_urls[:]
    c += 1
