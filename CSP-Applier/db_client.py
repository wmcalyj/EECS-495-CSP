import json
import urllib2
import urllib
import sys
import base64
import os
import urlparse
import logging
import math
import traceback
import tldextract
import template

logger = logging.getLogger('DOMCluster')
hdlr = logging.FileHandler('./logs/db_client.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.addHandler(consoleHandler)
logger.setLevel(logging.ERROR)

def writeTemplate(trees):
    try:
        host = "http://localhost:8880/templates"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')
        templates = {}
        for domain in trees:
            templates[domain] = {}
            if trees[domain] == None:
                templates[domain] = None
            elif isinstance(trees[domain], dict):
                for key in trees[domain]:
                    templates[domain][key] = trees[domain][key].dumps()

        data = { 'templates' : json.dumps(templates) }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        if rs['success']:
            logger.info("successfully write template at %s " % (rs['file_name']))
            return rs['file_name']
        else:
            logger.error("failed to write template %s " % (rs['message']))
            return None

    except Exception as e:
        logger.error("failed to write template %s " % (str(e)))
        return None


def fetchURLContents(url):
    try:
        host = "http://localhost:4040/api/web-contents/contents-fetch"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')

        if url != '*':
            url = urllib.quote_plus(url)
        data = { 'url' : url.strip() }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        decoded_rs = []
        if rs['success']:
            db_result = json.loads(rs['result'])
            print "get %d items "%(len(db_result))
            for item in db_result:
                if 'landing_url' in item:
                    u1 = urllib.unquote_plus(item['url'])
                    u2 = urllib.unquote_plus(item['landing_url'])
                    h1 = urlparse.urlparse(u1).netloc.strip().lower()
                    h2 = urlparse.urlparse(u2).netloc.strip().lower()
                    print "urlhost: %s vs landingurlhost: %s " %(h1, h2)
                    if h1 != h2:
                        continue
                decoded = base64.b64decode(item['contents'])
                #print "%s size: %d" %(item['url'],len(decoded))
                decoded_rs.append(decoded)
            if len(decoded_rs) == 0:
                return None
            return decoded_rs
        else:
            print "failed to fetch contents of url: "+url
            return None

    except Exception as e:
        print str(e)
        return None

def storeDistance(url1, url2, distance):
    try:
        host = "http://localhost:4040/api/web-contents/distance-store"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')

        if url1 != '*':
            url1 = urllib.quote_plus(url1)
        if url2 != '*':
            url2 = urllib.quote_plus(url2) 
        
        data = { 'url1' : url1.strip(), 'url2' : url2.strip(), 'distance' : str(distance) }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        if rs['success']:
            print "successfully store contents " + str(data)
            return True
        else:
            print "failed to store contents  "+ str(data)
            return False

    except Exception as e:
        print str(e)
        return False

def storeScripts(url, host_list, inline_list):
    try:
        host = "http://localhost:4040/api/web-contents/scripts-store"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')

        url = urllib.quote_plus(url)
        inline_list_encoded = [base64.b64encode(x) for x in inline_list]
        data = { 'url' : url.strip(), 
            'hosts' : host_list,
            'inlines' : inline_list_encoded }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        if rs['success']:
            #print "successfully store scripts for url %s " % url
            return True
        else:
            #print "failed to store scripts for url %s " % url
            return False

    except Exception as e:
        print >> sys.stderr, "Exception in storeScripts: "+str(e)
        return False

def storeTree(url, key, tree):
    try:
        host = "http://localhost:4040/api/web-contents/trees-store"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')
        domain = getEffectiveDomainFromURL(url)
        if domain == None:
            print "[storeTree] failed to get domain from url:", url
            return False
        url = urllib.quote_plus(url)
        data = { 'url' : url.strip(), 
            'key' : key,
            'tree' : tree,
            'domain' : domain }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        if rs['success']:
            print "successfully store tree %s for url %s " % (key, url)
            return True
        else:
            print "failed to store tree %s for url %s " % (key, url)
            return False

    except Exception as e:
        print >> sys.stderr, "Exception in storeTree: "+str(e)
        return False

def removeTree(domain, key):
    try:
        host = "http://localhost:4040/api/web-contents/trees-remove"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')
        data = { 'key' : key,
            'domain' : domain }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        if rs['success']:
            print "successfully remove tree %s for domain %s " % (key, domain)
            return True
        else:
            print "failed to remove tree %s for domain %s " % (key, domain)
            return False

    except Exception as e:
        print >> sys.stderr, "Exception in storeTree: "+str(e)
        return False

def fetchScripts(url):
    try:
        host = "http://localhost:4040/api/web-contents/scripts-fetch"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')

        if url != '*':
            url = urllib.quote_plus(url)

        data = { 'url' : url.strip() }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        final_rs = []
        if rs['success']:
            db_result = json.loads(rs['result'])
            if db_result == None or \
                not db_result['inlinescripts'] or not db_result['scripthosts']:
                #print "no scripts %s %s" %(str(db_result['inlinescripts']), str(db_result['scripthosts']))
                return None,None
            #print "get %d items %f" % (len(db_result), float(db_result[0]['distance']))
            try:
                inline_list = [base64.b64decode(x) for x in db_result['inlinescripts']]
            except UnicodeEncodeError as e:
                inline_list = db_result['inlinescripts']
            except TypeError as e:
                inline_list = db_result['inlinescripts']
            return db_result['scripthosts'], inline_list
        else:
            print "failed to fetch contents of url: "+url
            return None, None

    except Exception as e:
        #raise e
        traceback.print_exc(file=sys.stdout)
        print "Error:",str(e)
        return None, None

def fetchDistance(url1, url2):
    try:
        host = "http://localhost:4040/api/web-contents/distance-fetch"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')

        if url1 != '*':
            url1 = urllib.quote_plus(url1)
        if url2 != '*':
            url2 = urllib.quote_plus(url2) 

        data = { 'url1' : url1.strip(), 'url2' : url2.strip() }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        final_rs = []
        if rs['success']:
            db_result = json.loads(rs['result'])
            if db_result == None or len(db_result) == 0:
                #print "no distance %s" %(str(db_result))
                return None
            print "get %d items %f" % (len(db_result), float(db_result[0]['distance']))
            for item in db_result:
                final_rs.append(float(item['distance']))

            return final_rs
        else:
            print "failed to fetch contents of url: "+url
            return None

    except Exception as e:
        #raise e
        print str(e)
        return None

cacheTrees = {}
def fetchTrees(domain):
    try:
        host = "http://localhost:4040/api/web-contents/trees-fetch"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')
        domain = domain.strip().lower()
        data = { 'domain' : domain }
        if domain in cacheTrees:
            return cacheTrees[domain]

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        final_rs = {}
        if rs['success']:
            db_result = json.loads(rs['result'])
            if db_result == None or len(db_result) == 0:
                print "no trees for domain %s" %(domain)
                cacheTrees[domain] = None
                return None
            print "get %d trees for domain %s" % (len(db_result), domain)
            for item in db_result:
                final_rs[item['key'] ] = item['tree']
            cacheTrees[domain] = final_rs
            return final_rs
        else:
            print "failed to fetch tree of domain: "+domain
            cacheTrees[domain] = None
            return None

    except Exception as e:
        #raise e
        print "fetching tree exception: ",str(e)
        return None


def findAverageContents(arr):
    if arr==None or len(arr)==0:
        return None
    if len(arr) <= 2:
        return arr[0]

    #http://stackoverflow.com/questions/20811131/javascript-remove-outlier-from-an-array
    len_arr = sorted([len(x) for x in arr])
    q1 = len_arr[len(len_arr) / 4]
    q3 = len_arr[len(len_arr) * 3 / 4]
    iqr = q3 - q1

    new_arr = []
    max_value = q3 + iqr * 1.5
    min_value = q1 - iqr * 1.5
    #print max_value,min_value, iqr
    for item in len_arr:
        if item < max_value and item > min_value:
            new_arr.append(item)
    new_arr.sort()

    if len(new_arr) == 0:
        print "All data are are outliers"
        len_val = len_arr[len(len_arr)/2]
    else:
        len_val = new_arr[len(new_arr)/2]
    for item in arr:
        if len(item) == len_val:
            return item

def getEffectiveDomainFromURL(url):
  try:
    o = tldextract.extract(url.lower())
    return o.domain + '.' + o.suffix
  except Exception as e:
    print >> sys.stderr, "error in getting getEffectiveDomain ", str(e)
    return None

def main():
    '''
    #calc distance between any two urls in url file
    l = []
    f = open(sys.argv[1])
    for line in f:
        l.append(line.strip())
    findContentsFromURLList(l)
    '''

    #'''
    #fetch contents from url file
    #url_file = open(sys.argv[1])
    rs = fetchURLContents(sys.argv[1])
    print len(rs)
    '''
    for url in url_file:
        url = url.strip()
        rs = fetchURLContents(url)
        o = urlparse.urlparse(url)
        paths = o.path.split('/')
        dir_name = paths[-2]
        if len(dir_name.strip()) == 0:
            dir_name = "NEW_"+o.netloc +'_'+ paths[-1]
        path = os.path.join('./tmp',dir_name)
        if not os.path.exists(path):
            os.makedirs(path)    
        print "%s %d %s" %(url.strip(),len(rs),dir_name)
        count = 1
        for item in rs:
            file_path = os.path.join(path,'%d.txt'%count)
            f = open(file_path,'w')
            f.write(item+'\n')
            f.close()
            count += 1
    '''

    #client
    #storeScripts("http://www.example.com",\
    #    ["azone.com","b.com","ads.net"], \
    #    ["AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    #    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    #    "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"])
    #hosts, inlines = fetchScripts("http://www.sina.com.cn")
    #print len(hosts), len(inlines)

    #rs = fetchURLContents("*")
    #findContentsFromURLList(["http://www.google.com"])
    #print storeDistance("http://www.sina.com.cn","http://www.google.com",8.2)
    #print storeDistance("http://www.google.com","http://www.baidu.com",1.2)
    #print storeDistance("http://www.google.com","http://www.google.com",1.2)
    #print storeDistance("http://www.cnn.com","http://www.google.com",3.2)

    #print findAverageContents(["dsdsdsdsdsdsd","abc","dsdsdsdsdsdWWW"])

    '''
    rs = fetchDistance("http://www.google.com","http://www.sina.com.cn")
    rs = fetchDistance("*","*")
    for item in rs:
        print "%f " %item

    o = urlparse.urlparse(sys.argv[1])
    dir_name = o.path.replace('/','_')

    path = os.path.join('./tmp',dir_name)
    if not os.path.exists(path):
        os.makedirs(path)

    count = 1
    for item in rs:
        file_path = os.path.join(path,'%d.txt'%count)
        f = open(file_path,'w')
        f.write(item+'\n')
        f.close()
        count += 1
    '''

if __name__=="__main__":
    main()