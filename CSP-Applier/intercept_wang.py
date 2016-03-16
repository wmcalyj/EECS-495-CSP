import sys, traceback
sys.path.append(".")
sys.path.append("/Library/Python/2.7/site-packages")

from hashlib import sha1
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from libmproxy.protocol.http import decoded
from csp_applier import html, template
from dom_analyzer import DOMAnalyzer
from db_client import writeTemplate
from template import getTreesForDomainFromDB
from time import time


def start(context, argv):
    if len(argv) < 2:
        raise ValueError('Usage: -s "intercept.py enable_update(true|false) (pre_fetched_domain)"')

    if len(argv) == 3:
        context.trees = {}
        treedict = getTreesForDomainFromDB(argv[2].lower())
        context.trees[argv[2].lower()] = treedict

    else:
        context.trees = {}
    #context.http_path, context.file_path = argv[1], argv[2]
    if argv[1].lower() == 'true':
        context.enable_update = True
    elif argv[1].lower() == 'false':
        context.enable_update = False
    else:
        raise ValueError('Usage: -s "intercept.py enable_update(true|false)"')
    #content = open('./logs/log').read()
    #fw = open('')
    context.f = open('./logs/log','a')
    

#determin iframe, ignore iframe
def response(context, flow):
    try:
        url = flow.request.url
        context.f.write('receive response: %s\n'%flow.request.url)
        with decoded(flow.response):  # Automatically decode gzipped responses.
            if (not "Content-Type" in flow.response.headers) or \
                len(flow.response.headers) == 0:
                return
            tp = flow.response.headers["Content-Type"][0].lower()
            #context.f.write('  type:%s\n' %tp)
            if url.endswith('json'):
                return
            #Only for evaluation!!!!!!!
            if flow.request.headers['Referer']:
                return
            if "text/html" in tp:
                flow.response.headers['Content-Security-Policy'] = \
                    #["default-src 'self' 'unsafe-eval' *; style-src 'self' 'unsafe-eval' 'unsafe-inline' *"]
                    ["default-src 'self'; style-src 'self' 'unsafe-eval' 'unsafe-inline' *"]
                flow.response.headers['Cache-Control'] = ["no-cache"]
                #context.f.write('  rewrite response %s %s\n' % (flow.request.url, \
                #    str(flow.response.headers) ) )
                t1 = time()
                try:
                    soup = BeautifulSoup( flow.response.content, "html5lib")
                except Exception as e:
                    soup = BeautifulSoup( flow.response.content, 'lxml')
                analyzer = DOMAnalyzer(soup, \
                    'https://localhost:4433/allowed-resources/', \
                    './js_repository/', context.trees, flow.request.url, context.enable_update)
                t2 = time()
                t = (t2 - t1)*1000
                context.f.write("DOMTREE_PARSE_TIME: %f ms\n" %(t))
                analyzer.process()
                
                #context.f.write('write template: \n')
                #template_file_name = writeTemplate(context.trees)
                #context.f.write('write template: '+str(template_file_name)+'\n')
                #if template_file_name != None:
                #    template_src = "https://localhost:4433/allowed-resources/"+template_file_name
                #    template_node = soup.new_tag("script", src=template_src)
                #    analyzer.soup.head.insert(1, template_node)
                client_lib_node = soup.new_tag("script", src="https://localhost:4433/libs/client_lib.js")
                esprima_node = soup.new_tag("script", src="https://cdn.rawgit.com/jquery/esprima/1.2/esprima.js")
                analyzer.soup.head.insert(1, client_lib_node)
                analyzer.soup.head.insert(1, esprima_node)
                #try:
                #    context.f.write('  OLD response %s:\n' % soup.prettify().encode('ascii', 'ignore'))
                #except Exception as e:
                #    context.f.write('  display response error %s\n' %(str(e)) )
                #context.f.write("    debug before analyzing\n")
                #context.f.write("    debug after analyzing %d\n" %(len(html_parser)) )
                
                #context.f.write("  need write %d inlines \n" %(len(analyzer.inlines)) )
                #new_content = UnicodeDammit(analyzer.soup.prettify())
                #flow.response.content = new_content.unicode_markup
                try:
                    flow.response.content = analyzer.soup.prettify().encode('utf-8')
                    #context.f.write('newcontent:%s\n' %flow.response.content)
                except Exception as e:
                    context.f.write("  encoding exception: %s\n" %(str(e)))
                t3 = time()
                t = (t3 - t2) * 1000
                context.f.write("REWRITE_TIME: %f ms\n" %(t))
                #context.f.write("  new HTML:\n %s  \n" %(flow.response.content) )
            else:
                pass
                #context.f.write('NOT rewriting %s %s response\n' % (flow.request.url,\
                #    flow.response.headers["Content-Type"]) )
            context.f.write('\n')
            
    except Exception as e:
        context.f.write('exception at %s for error: %s\n' %(url, str(e)))
        traceback.print_exc(file=context.f)

