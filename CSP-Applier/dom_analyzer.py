from bs4 import BeautifulSoup
from template import getTreesForDomainFromDB
from template import updateTreeForDomain
from bs4 import NavigableString
from urlparse import urlparse
from uuid import uuid4
from trees import matchTreesFromDomainWithScript
import logging, sys, re, tldextract, json, urllib, hashlib, os, time,traceback

logger = logging.getLogger('HTMLParser')
hdlr = logging.FileHandler('./logs/html_parser2.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(hdlr) 
#logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)

class DOMAnalyzer:
	
	__events = [
        # Mouse Events
        "onclick", "ondblclick", "onmousedown", "onmousemove", "onmouseover", "onmouseout", "onmouseup",
        # Keyboard Events
        "onkeydown", "onkeypress", "onkeyup",
        # Frame/Object Events
        "onabort", "onerror", "onload", "onresize", "onscroll", "onunload",
        # Form Events
        "onblur", "onchange", "onfocus", "onreset", "onselect", "onsubmit"
    ]

	def __init__(self, soup, local_url, dest_dir, trees={}, page_url='undefined', enable_update = False):
		self.soup = soup
		self.inlines = {}
		self.externals = []
		self.script_tags = []
		self.url = page_url
		self.local_url = \
			local_url if (local_url[-1]=='/') else (local_url+'/')
		self.dest_dir = dest_dir
		self.attr_js = []
		self.trees = trees
		self.enable_update = enable_update

		m = hashlib.md5()
		m.update(page_url)
		self.urlhash = m.hexdigest()

	def process(self):
		self.inlines = {}
		self.externals = [] # for debugging use
		self.remove_tags = []
		self.clear_tags = []
		self.attr_js = []

		logger.info('  [DEBUG] start processing %s' %self.url)
		self._traverse(self.soup, None, 0)
		logger.info('  [DEBUG] finish traversing %s' %self.url)
		
		try:
			[tag.decompose() for tag in self.remove_tags]
			[tag.clear() for tag in self.clear_tags]
		except Exception as e:
			logger.error('  [ERROR] removing/clearing tag node: %s' %str(e))

		logger.info('  [DEBUG] finish clearing/removing DOM, cleared %d tags and removed %d tags' \
			%(len(self.clear_tags), len(self.remove_tags)))

		# write inlines
		for key in self.inlines:
			#logger.error('  [DEBUG] sc contents: %s' %self.inlines[key] )
			if not self._write_external_script(key, self.inlines[key]):
				logger.error('  [ERROR] failed to write external script: %s' %str(self.inlines[key]) )
			else:
				logger.info('  [DEBUG] finish writing external script: \
					%s size: %d' %(key, len(self.inlines[key])) )
		logger.info('  [DEBUG] processing result: %d inlines and %d externals' \
			%(len(self.inlines), len(self.externals)))

		# process event listeners
		inline_event_listeners = []
		for item in self.attr_js: #(id, event, script)
			sc = self._wrap_event_listener(item[0], item[1], item[2])
			if sc == None:
				continue
			inline_event_listeners.append(sc)

		if len(inline_event_listeners) > 0:
			try:
				full_listeners = \
					"document.addEventListener('DOMContentLoaded', function () { %s } );\r\n"
				full_listeners = full_listeners % ( '\r\n'.join(inline_event_listeners) )
				logger.info("Full_listerns!!!!!!!!!!!!!!!! " + full_listeners)
				file_name = 'script_%s_%s_event.js' %(uuid4().hex, self.urlhash)
				self._write_external_script(file_name, full_listeners)
				# modify html page
				new_tag = self.soup.new_tag('script',src=self._build_local_url_path(file_name))
				self.soup.head.insert(1, new_tag)
				logger.info('  [DEBUG] finish processing inline event listeners: %s\n' %full_listeners)
			except Exception as e:
				logger.error('  [ERROR] error in generating event listener: %s' %(str(e)))

	def _traverse(self, root, parent_node, level):
		#print "traverse: ",str(root)
		if root == None:
			return ""

		if isinstance(root, NavigableString):
			rs = root.string
			if rs == None:
				return None
				
			try:
				rs = rs.encode('utf-8').strip()
			except Exception as e:
				logger.error('_traverse error in encoding: %s' %(str(e)))
			return rs

		external = None
		inline = None
		try:
			#logger.debug("NAME:%s TYPE:%s" %(root.name, str(root.get('type')) ) )
			tag = root.name.lower()
			if tag == 'script':
				if root.get('src') != None:
					external = root.get('src').strip().lower()
					if not self._check_url(external):
						self.remove_tags.append(root)
				#inline script
				elif isinstance(root.contents[0], NavigableString):
					inline = self._traverse(root.contents[0], root, level+1)
					if inline == None:
						logger.debug('  [ERROR] None inline contents: %s' %root)
					rs = self._check_inline_script(inline)
					self.clear_tags.append(root)
					if rs == None:
						logger.info('  [ERROR] Script failed checking: %s' % self._encode_script(inline) )
					else:					
						file_name = 'script_%d_%s_inline.js' %(len(self.inlines), self.urlhash)
						root['src'] = self._build_local_url_path(file_name)
						self.inlines[file_name] = rs
						logger.info('  [DEBUG] script %s'%str(inline))
						logger.info('  [DEBUG] convert inline to external scripts: %s <= %s' \
							% (file_name, self._encode_script(inline)) )
				else:
					logger.error("  [ALERT] unknown script tag: "+str(tag)) 
				# for debugging
				if external != None:
					self.externals.append(external)
			
			for event in self.__events:
				if root.has_attr(event):
					if not root.has_attr('id'):
						root['id'] = uuid4().hex
					tag_id = root['id']
					script = root[event]
					del root[event]
					self.attr_js.append((tag_id, event, script))
					logger.debug("  [DEBUG] inline event listener: %s" %str((tag_id, event, script))) 

		except Exception as e:
			logger.error("  [SEVERE ERROR]: %s" % ( str(e)+" "+root.name))
			traceback.print_exc(file=open('./logs/error','w'))

		for child in root.contents:
			self._traverse(child, root, level+1)

	def _wrap_event_listener(self, tag_id, event, body):
		try:
			#fun_name = 'csp_%s_%s' %(tag_id, event)
			#listener = "var %s = function() { %s }; \r\n" \
			#	%(fun_name, body)

			call_stat = \
				"try { \r\n" + \
					"" +\
					"document.getElementById('%s')" + \
					".addEventListener('%s', function () { %s }); \r\n" + \
				"} catch(e) {console.log('Error CSP_APPLIER'+str(e) );}\r\n"
			call_stat = call_stat % (tag_id, event[2:], body)
		except Exception as e:
			logger.error('error in _wrap_event_listener: %s ' %(str(e)))
			return None

		return call_stat

	def _build_local_url_path(self, full_name):
		return self.local_url + full_name

	def _encode_script(self, script):
		rs  = None
		try:
			try:
				rs = script.encode('utf-8', 'ignore').strip()
			except UnicodeEncodeError:
				#logger.debug('UnicodeEncodeError failed encoding utf-8')
				rs = unicode(script)
			except UnicodeDecodeError:
				#logger.debug('UnicodeDecodeError failed encoding utf-8')
				rs = script				
		except Exception as e:
			logger.error(' [ERROR] %s failed encoding script:%s %s' %(e.__class__.__name__, str(script), str(e)))
			logger.error("  detailed information", exc_info=True)
			#raise
		return rs

	# TODO: not implemented
	def _check_url(self, url):
		return True
		'''
		try:
			domain = self._get_effective_domain(url)
			logger.debug('_check_url: find domain: %s' %(domain))
			if domain == None:
				return True
			else:
				# add template matching methods here
				return True
		except Exception as e:
			return False
		'''

	# TODO: not implemented
	def _check_inline_script(self, content):
		return content
		'''
		t1 = time.time()
		domain = self._get_effective_domain(self.url)
		if domain in self.trees and not self.enable_update:
			allowed, failed, tree, failed_trees = matchTreesFromDomainWithScript(domain, content, self.trees[domain])
			if allowed == None or failed == None:
				return content
			logger.info("1 allowed: %d, failed: %d" %(len(allowed), len(failed)))
		else:
			allowed, failed, tree, failed_trees = matchTreesFromDomainWithScript(domain, content)
			self.trees[domain] = tree
			if allowed == None or failed == None:
				return content
			logger.info("2 allowed: %d, failed: %d" %(len(allowed), len(failed)))
		t2 = time.time()
		logger.debug("_check_inline_script time: %f %s %d" \
			%((t2 - t1), str(self.enable_update), len(failed_trees) ) )
		
		if self.enable_update:
			for tree in failed_trees:
				logger.debug("prepare update tree: "+tree.dumps())
				if not updateTreeForDomain(self.url, domain, tree):
					logger.error("failed to update tree!!!")
				else:
					logger.info("succeeded to update tree!!!")
		
		#NOTE: if too bad, enable this
		return content

		#There has some bugs in splitting the codes....
		#if len(failed_trees) == 0:
		#	return content
		#else:
		#	return '\r\n'.join(allowed)
		'''

	def _write_external_script(self, file_name, contents):
		try:
			full_path = os.path.join(self.dest_dir, file_name)
			logger.info("  _write_external_script contents :%s"%contents)
			rs = self._encode_script(contents)
			if rs == None:
				logger.error('  [ERROR] _write_external_script failed: encoding contents failed')
				return False
			fw = open(full_path, 'w')
			fw.write("// CSP-Applier: Script - " + self.url + " \r\n")
			fw.write("%s\r\n" % (rs))
			fw.close()
			return True
		except Exception as e:
			logger.error('  [ERROR] _write_external_script failed: %s' %str(e))
			return False

	def _get_effective_domain(self, url):
		try:
			url = urllib.unquote_plus(url.lower())
			no_fetch_extract = tldextract.TLDExtract(suffix_list_url=False)
			o = no_fetch_extract(url)
			return o.domain + '.' + o.suffix
		except Exception as e:
			logger.error("  [ERROR]error in getting getEffectiveDomain %s" %str(e))
			return None

def main():
	t1 = time.time()
	url = 'https://www.cnn.com'
	tldextract.TLDExtract(suffix_list_url=False)
	o = tldextract.extract(url)
	domain = o.domain + '.' + o.suffix
	domain_trees = getTreesForDomainFromDB(domain)
	trees = {}
	trees[domain] = domain_trees
	contents = open(sys.argv[1]).read()
	#print contents
	logger.debug('url:%s domain:%s' %(url, domain))
	t2 = time.time()
	try:
		soup = BeautifulSoup( contents, "html5lib")
	except Exception as e:
		soup = BeautifulSoup( contents, 'lxml')
	analyzer = DOMAnalyzer(soup, \
		'https://localhost:4433/allowed-resources/', './js_repository/', trees, url)
	analyzer.process()
	t3 = time.time()
	logger.debug("time difference: DOM:%f, whole:%f" %((t3-t2), (t3-t1)))
	#logger.debug('NEXT ROUND')
	#analyzer.process()
	new_tag = soup.new_tag("script", src="https://localhost:4433/libs/client_lib.js")
	analyzer.soup.head.insert(1, new_tag)
	#print analyzer.soup.prettify().encode('utf-8')
	#print soup.prettify().encode('utf-8')

if __name__ == "__main__":
	main()

	'''
	def extract_js(self):
		external_js = []
		inline_js = []
		for tag in self.soup.find_all('script'):
		    if tag.has_attr('src'):
		        external_js.append((tag['src'], tag, uuid4().hex))
		    elif tag.has_attr('type') and tag["type"] != "text/html":
		        logger.debug('[INLINE SCRIPT]: %s' %str(tag) )
		        inline_js.append((tag, uuid4().hex))

		attr_js = []
		for listener in self.__events:
		    for tag in self.soup.find_all(True):
		        if tag.has_attr(listener):
		            attr_js.append((listener, tag, uuid4().hex))
		logger.debug('[JS SUMMARY] %d inline, %d external, %d attrs' \
		    %(len(inline_js), len(external_js), len(attr_js) ) )

		self.external_js = external_js
		self.inline_js = inline_js
		self.attr_js = attr_js
	'''