import sys, traceback
sys.path.append(".")
sys.path.append("/usr/local/lib/python2.7/site-packages")

from hashlib import sha1
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from libmproxy.protocol.http import decoded
from csp_applier import html, template
from dom_analyzer import DOMAnalyzer
from db_client import writeTemplate
from template import getTreesForDomainFromDB
from time import time
from urlparse import urlparse

def start(context, argv):
    if len(argv) < 2:
        raise ValueError('Usage: -s "intercept.py enable_update(true|false) (pre_fetched_domain)"')

    # Prefetch trees for domain
    if len(argv) == 3:
        context.trees = {}
        treedict = getTreesForDomainFromDB(argv[2].lower())
        context.trees[argv[2].lower()] = treedict
    else:
        context.trees = {}
    
    # indicate whether enable update
    if argv[1].lower() == 'true':
        context.enable_update = True
    elif argv[1].lower() == 'false':
        context.enable_update = False
    else:
        raise ValueError('Usage: -s "intercept.py enable_update(true|false)"')

    # opens logging file
    context.f = open('./logs/log','w')
    

#determin iframe, ignore iframe
def response(context, flow):
    try:
        url = flow.request.url
        o = urlparse(url)
        host = o.netloc.lower()
        if host.startswith("localhost") or host.startswith("127.0.0.1"):
            return
        context.f.write('Receive response: %s\n'%flow.request.url)
        #context.f.write('  headers: %s\n' % str(flow.response.headers) )
        if not "Content-Type" in flow.response.headers:
            return
        content_type = flow.response.headers["Content-Type"][0].lower()
        if not "text/html" in content_type:
            return
        elif url.endswith('json'):
            return

        with decoded(flow.response):  # Automatically decode gzipped responses.
            #if flow.request.headers['Referer']:
            #    return
            flow.response.headers['Content-Security-Policy'] = \
                ["default-src * data: 'self' ; style-src data: 'self' 'unsafe-eval' 'unsafe-inline' *"]
            flow.response.headers['Cache-Control'] = ["no-cache"]
            
            context.f.write('  start rewriting response %s %s\n' % (flow.request.url, \
                str(flow.response.headers) ) )
            
            try:
                soup = BeautifulSoup( flow.response.content, "html5lib")
            except Exception as e:
                soup = BeautifulSoup( flow.response.content, 'lxml')
            
            analyzer = DOMAnalyzer(soup, \
                'https://localhost:4433/allowed-resources/', \
                './js_repository/', context.trees, flow.request.url, context.enable_update)
            analyzer.process()
            
            client_lib_node = soup.new_tag("script", src="https://localhost:4433/libs/client_lib.js")
            esprima_node = soup.new_tag("script", src="https://cdn.rawgit.com/jquery/esprima/1.2/esprima.js")
            analyzer.soup.head.insert(1, client_lib_node)
            analyzer.soup.head.insert(1, esprima_node)
           
            try:
                flow.response.content = analyzer.soup.prettify().encode('utf-8')
                context.f.write('newcontent:%s\n' %flow.response.content)
            except Exception as e:
                context.f.write("  encoding exception: %s\n" %(str(e)))
            #context.f.write("  new HTML:\n %s  \n" %(flow.response.content) )
            context.f.write('\n')
            
    except Exception as e:
        context.f.write('Exception at %s for error: %s\n' %(url, str(e)))
        traceback.print_exc(file=context.f)

