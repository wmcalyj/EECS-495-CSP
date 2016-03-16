from db_client import storeScripts
from db_client import storeTree
from db_client import fetchTrees
from db_client import fetchScripts
from db_client import fetchURLContents
from db_client import findAverageContents
from script_analyzer import analyzeJSCodesFinerBlock
from script_analyzer import analyzeJSON
from html_parser import traverseDOMTree
from html_parser import getLDPairRepr
from template import getTreesForDomainFromDB
from template import TemplateTree
from node_pattern import global_count
from utilities import displayErrorMsg
from base64 import b64encode
from base64 import b64decode
import sys, os, re, json, hashlib, uuid

###################MATCH##############
def compare(treedict, target_tree):
  key = target_tree.key
  if key in treedict:
    tree = treedict[key]
    return tree.match(target_tree)

def simpleCompare(treedict, target_tree):
  return target_tree.key and target_tree.key in treedict

def matchScriptsFromURLFileWithDomainTemplate(domain, url_list_path):
  treedict = getTreesForDomainFromDB(domain)
  if treedict == None or len(treedict) == 0:
    print "failed to fetch trees for domain ", domain
    return None, None
  passed_sc = []
  failed_sc = []
  f = open(url_list_path)
  for line in f:
    url = line.strip()
    print "process url "+url
    hosts, inlines = fetchScripts(url)
    if inlines==None or len(inlines) ==0:
      print "no inlines for "+url
      continue
    for inline in inlines:
      passed, failed = matchScriptWithDomainTemplate(domain, inline, treedict)
      if passed == None:
        print "failed for inline [S] ", inline[:100],' [E]'
      else:
        passed_sc += passed
        failed_sc += failed
  rate = float(len(passed_sc))/float(len(passed_sc)+len(failed_sc))
  print "passed %d; failed: %d; rate:%f" %(len(passed_sc), len(failed_sc), rate)
  print "match details : ", str(global_count)

def matchScriptWithDomainTemplate(domain, script, treedict = None):
  if treedict == None:
    treedict = getTreesForDomainFromDB(domain)
  if treedict == None or len(treedict) == 0:
    print "failed to fetch trees for domain ", domain
    return None, None
  #print "fetched %d trees for domain" %(len(treedict))
  
  is_json = False
  rs, sc = analyzeJSCodesFinerBlock(script)
  if rs == None:
    rs = analyzeJSON(script)
    is_json = True
  if rs == None:
    print "no script nor json"
    return [], []

  allowed_sc = []
  failed_sc = []

  if is_json:
    tree = TemplateTree(rs, None)
    #if simpleCompare(treedict, tree):
    if compare(treedict, tree):
      allowed_sc.append(rs)
      print "JSON allowed "
    else:
      failed_sc.append(rs)
      print "JSON failed "
  else:
    print "generate %d subtrees for target script" %(len(rs))
    for index in range(len(rs)):
      seq = rs[index]
      tree = TemplateTree(seq, None)
      key = tree.key

      #if simpleCompare(treedict, tree):
      if compare(treedict, tree):
        allowed_sc.append(sc[index])
      else:
        failed_sc.append(sc[index])

    print "allowed %d blocks, failed %d blocks" %(len(allowed_sc), len(failed_sc))
  return allowed_sc, failed_sc


######################################

###################EXTRACTION SCRIPT##########################

def extractionHelper(root, result, script_hosts, script_contents):
  #result.append(root)
  if root.tag == "script":
    if root.src != "None":
      script_hosts.add(root.src)
    elif root.val != "":
      script_contents.add(root.val)
      #if 'json' in root.tp:
      # try:
      #   json.loads(root.val)
      #   script_contents.add((root.val,"json"))
      # except Exception as e:
      #   script_contents.add((root.val,"script"))
      #else:
      # script_contents.add((root.val,"script"))

  for child in root.children:
    extractionHelper(child, result, script_hosts, script_contents)

def extractScriptFromDOMTree(root):
  result = [None]
  script_hosts = set()
  script_contents = set()
  extractionHelper(root, result, script_hosts, script_contents)
  return script_hosts, script_contents

def extractScriptFromContents(contents):
  if contents == None or len(contents)==0:
    return None, None
  try:
    soup = BeautifulSoup(contents, "html5lib")
  except Exception as e:
    print "Error parsing DOM using html5 ",str(e)
    soup = BeautifulSoup(contents.decode('utf-8'), "html5lib")
  node = Node("doc")
  traverseDOMTree(soup.html,node, 0)
  script_hosts, script_contents = extractScriptFromDOMTree(node)
  
  #for host in script_hosts:
  # print "host: %s" %host
  #for content in script_contents:
  # print "content: %s" %content
  #print "summary Host:%d Contents:%d" %(len(script_hosts), len(script_contents))

  return script_hosts, script_contents

def extractAndStoreScriptsFromDOM(url, dom):
  hostset, contset = extractScriptFromContents(dom)
  host_list = []
  cont_list = []
  for item in hostset:
    try:
      new_item = item.encode('utf-8')
      host_list.append(new_item)
    except Exception as e:
      displayErrorMsg('extractAndStoreScriptsFromDOM',\
        "decoding error: "+str(e))
      host_list.append(item)

  for item in contset:
    try:
      new_item = item.encode('utf-8')
      cont_list.append(new_item)
    except Exception as e:
      displayErrorMsg('extractAndStoreScriptsFromDOM',\
        "decoding error: "+str(e))
      cont_list.append(item)
  displayErrorMsg('extractAndStoreScriptsFromDOM',\
    "extracted %d script hosts and %d inline scripts for %s " \
      %(len(host_list), len(cont_list), url))

  if storeScripts(url, host_list, cont_list):
    print "successfully store %s scripts to DB " %url
  else:
    print "failed to store %s scripts to DB " % url

def extractAndStoreScriptsFromFileList(file_list_path):
  f = open(file_list_path)
  urls = set()
  for line in f:
    urls.add(line.strip())

  for url in urls:
    print "prcossing scripts of %s " % url
    hosts, inlines = fetchScripts(url)
    if hosts == None or inlines == None:
      contents = fetchURLContents(url)
      if contents == None or len(contents) == 0:
        print >> sys.stderr, "%s doesn't have contents " %url
        continue
      content = findAverageContents(contents)
      if content == None:
        print >> sys.stderr, "failed to extract average content for %s" %url
        continue
      extractAndStoreScriptsFromDOM(url, content)

    else:
      print "%s already has %d hosts and %d inline scripts " \
        %(url, len(hosts), len(inlines))   

#####################END######################################

#################FETCH CONTENTS###############################

def findContentsFromURLList(urllist):
    list_len = len(urllist)
    for i in range(list_len):
        for j in range(i+1, list_len):
            #print "1 %d %d" %(i,j)
            url1 = urllist[i]
            url2 = urllist[j]
            #print "2 %d %d" %(i,j)
            if url1 == url2:
                continue
            rs = fetchDistance(url1, url2)
            if rs == None or len(rs) == 0:
                #print "3 %d %d" %(i,j)
                contents1 = fetchURLContents(url1)
                contents2 = fetchURLContents(url2)
                c1 = findAverageContents(contents1)
                c2 = findAverageContents(contents2)
                if c1 == None :
                    logger.debug("[alert] [%s] has no contents" %url1 )
                    continue
                if c2 == None :
                    logger.debug("[alert] [%s] has no contents" %url2 )
                    continue  
                #print "4 %d %d" %(i,j)
                distance = calcTwoHTMLDistance(c1, c2)
                #print "5 %d %d" %(i,j)
                r = storeDistance(url1, url2, distance)
                logger.debug("calculate distance [%s][%s]: %f %s" %(\
                    url1, url2, distance, r) )
            else:
                #print "6 %d %d %s" %(i,j,str(rs))
                logger.debug("find distance [%s][%s]: %f " %(\
                    url1, url2, rs[0]) )

######################END#####################################

####################DOM TREE DISTANCE CALC#####################

def calcTwoHTMLDistanceFromFiles(dom_path1, dom_path2): 
  contents1 = open(dom_path1).read()
  contents2 = open(dom_path2).read()
  calcTwoHTMLDistance(contents1,contents2)

def calcTwoHTMLDistance(contents1, contents2):
  try:
    soup1 = BeautifulSoup(contents1, "html5lib")
  except Exception as e:
    print "Error parsing DOM using html5 ",str(e)
    soup1 = BeautifulSoup(contents1.decode('utf-8'), "html5lib")
  
  try:
    soup2 = BeautifulSoup(contents2, "html5lib")
  except Exception as e:
    print "Error parsing DOM using html5 ", str(e)
    soup2 = BeautifulSoup(contents2.decode('utf-8'), "html5lib")

  node1 = Node("doc")
  node2 = Node("doc")
  traverseDOMTree(soup1.html,node1, 0)
  traverseDOMTree(soup2.html,node2, 0)
  ld1, ld1_script_hosts, ld1_script_contents = getLDPairRepr(node1)
  ld2, ld2_script_hosts, ld2_script_contents = getLDPairRepr(node2)
  print "script length for ld1: %d %d " % (len(ld1_script_hosts),len(ld1_script_contents))
  print "script length for ld2: %d %d " % (len(ld2_script_hosts),len(ld2_script_contents))
  D = mmdiff(ld1, ld2)
  return mmdiffR(ld1, ld2, D, \
    ld1_script_hosts,ld1_script_contents, ld2_script_hosts, ld2_script_contents)
######################END######################################

def main():
  #fetchAndProcessScriptsOfURLsFromFile(sys.argv[1],sys.argv[2])
  matchScriptsFromURLFileWithDomainTemplate(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
  main()
