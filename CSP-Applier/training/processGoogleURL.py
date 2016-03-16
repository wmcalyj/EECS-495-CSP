from urlparse import urlparse
from urllib import unquote_plus
import sys
import HTMLParser, tldextract
html_parser = HTMLParser.HTMLParser()

def decodeURL(url):
  url = url.lower()
  unquote_url = unquote_plus(url)
  unescape_url = html_parser.unescape(unquote_url)
  return unescape_url

def generateGoogleURLKey(url):
  url = decodeURL(url)
  o = urlparse(url)
  if "aclk" in o.path and \
    "adurl=" in o.query:
    return None
  query = None
  if o.query != "":
    tmp = o.query.split('&')
    for item in tmp:
      if item.startswith('q='):
        query = item.strip()
        break
  if query != None:
    url = o.scheme + "://" + o.netloc + o.path +'&'+query
  else:
    url = o.scheme + "://" + o.netloc + o.path
  return url

def preProcessGoogleURLList(url_list):
  url_dict = {}
  for url in url_list:
    key = generateGoogleURLKey(url)
    if key == None:
      continue
    if key in url_dict:
      continue
    url_dict[key] = url
  return url_dict

def getEffectiveDomainFromURL(url):
  try:
    o = tldextract.extract(url.lower())
    return o.domain + '.' + o.suffix
  except Exception as e:
    print >> sys.stderr, "error in getting getEffectiveDomain ", str(e)
    return None

def getEssentialPartOfURL(url):
  try:
    o = urlparse(url)
    return o.scheme + "://" + o.netloc + o.path 
  except Exception as e:
    print >> sys.stderr, "error in getting getEssentialPartOfURL ", str(e)
    return None

def preProcessRegularURLLlist(main_url, url_list):
  main_domain = getEffectiveDomainFromURL(main_url)
  if main_domain == None or url_list == None:
    return None
  url_set = set()
  for url in url_list:
    domain = getEffectiveDomainFromURL(url)
    #print "domain %s of %s " %(domain, url)
    if domain == None or domain != main_domain:
      continue
    u = getEssentialPartOfURL(url)
    if u == None:
      continue
    url_set.add(u)    
  return url_set

def main():
  f = open(sys.argv[1])
  fw = open(sys.argv[2],'w')
  url_list = []
  for line in f:
    line = line.strip()
    url_list.append(line)
  print "Read %d lines of urls" %(len(url_list))

  '''
  #Google process
  url_dict = preProcessGoogleURLList(url_list)
  print "After processing, generating %d lines of urls" %(len(url_dict))
  for k in url_dict:
    fw.write(url_dict[k]+'\n')
  '''
  #regular process
  
  url_set = preProcessRegularURLLlist(url_list[0], url_list)
  print "After processing, generating %d lines of urls" %(len(url_set))
  for k in url_set:
    fw.write(k+'\n')
  
  fw.close()
  f.close()

if __name__=="__main__":
  main()
    
