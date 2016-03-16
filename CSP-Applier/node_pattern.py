import sys, re, tldextract, json, urllib, logging
from enum import Enum
from urlparse import urlparse
from base64 import b64encode
from base64 import b64decode

MIN_SAMPLE_SIZE = 5
ENUM_THRESHOLD = 0.3
PATTERN_MIN_PREFIX = 3

'''
	Exports:
		1. NodePattern generateNodePattern(sample_list)
		2. class NodePattern
'''

class StringType(Enum):
  CONST = "CONST"
  ENUM = "ENUM"
  NUMBER = "NUMBER"
  QUOTED_NUMBER = "QUOTED_NUMBER"
  URI = "URI"
  OTHER = "OTHER"
  INSUFFICIENT = "INSUFFICIENT"

StringTypeDict = {\
	'INSUFFICIENT' : StringType.INSUFFICIENT,\
  'CONST' : StringType.CONST, \
  'ENUM' : StringType.ENUM, \
  'NUMBER' : StringType.NUMBER, \
  'QUOTED_NUMBER' : StringType.QUOTED_NUMBER, \
  'URI' : StringType.URI, \
  'OTHER' : StringType.OTHER}

global_count = {'INSUFFICIENT': 0, \
								'TARGET_VAL_NULL':0, \
								'PASS':0,'FAIL':0}

logger = logging.getLogger('HTMLParser')
hdlr = logging.FileHandler('./logs/html_parser2.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.addHandler(consoleHandler)
logger.setLevel(logging.ERROR)

class NodePattern():
	def __init__(self, tp=StringType.INSUFFICIENT, val=None):
		self.tp = tp
		self.val = val
	
	def is_insufficient(self):
		return self.tp == StringType.INSUFFICIENT

	def match(self, val_str):
		if val_str.replace('"','').replace("'",'') == '':
			#logger.debug("[COMPARE] TARGET VAL is empty ") 
			global_count['TARGET_VAL_NULL'] += 1
			return True
		if self.tp == StringType.INSUFFICIENT:
			if val_str in self.val:
				#logger.debug("[COMPARE] MATCH INSUFFICIENT")
				pass
			else:
				debug_str = "Length:[%d][%s] Vals:[%s]" %(len(self.val),str(self.val), str(self.val))
				#print "[COMPARE] INSUFFICIENT is insufficient: %s" %debug_str
				global_count['INSUFFICIENT'] += 1
			return True
		elif self.tp == StringType.CONST:
			if self.val != val_str:
				logger.debug('[COMPARE] CONST error %s vs %s ' %(str(self.val), str(val_str)))
				global_count['FAIL'] += 1
				return False
		elif self.tp == StringType.ENUM:
			if val_str not in self.val:
				logger.debug("[COMPARE] ENUM error %s not in %s " %(str(val_str), str(self.val)))
				global_count['FAIL'] += 1
				return False
		elif self.tp == StringType.NUMBER:
			if not stringIsNumeric(val_str):
				logger.debug("[COMPARE] NUMBER error %s not a number " %(val_str))
				global_count['FAIL'] += 1
				return False
		elif self.tp == StringType.QUOTED_NUMBER:
			if not stringIsNumeric(val_str[1:-1]):
				logger.debug("[COMPARE] QUOTED_NUMBER error %s not a quoted number " %(val_str))
				global_count['FAIL'] += 1
				return False
		elif self.tp == StringType.URI:
			d_set = getDomainsFromString(val_str)
			if not d_set.issubset(self.val):
				logger.debug("[COMPARE] URI error %s not a subset of %s " %(str(val_str), str(self.val) ))
				global_count['FAIL'] += 1
				return False
		elif self.tp == StringType.OTHER:
			if not self.val.check(val_str):
				logger.debug("[COMPARE] OTHER error %s not meeting rq of %s" \
					%(val_str, self.val.dumps()))
				global_count['FAIL'] += 1
				return False
		global_count['PASS'] += 1
		return True

	def update(self, val_str):
		try:
			if val_str.replace('"','').replace("'",'') == '':
				logger.info("[UPDATE] TARGET VAL is empty [%s] "%val_str)
				return
			if self.tp == StringType.INSUFFICIENT:
				self.val.append(val_str)
				if len(self.val) > MIN_SAMPLE_SIZE:
					new_node = generateNodePattern(self.val)
					self.tp = new_node.tp
					self.val = new_node.val
					logger.info("[UPDATE] INSUFFICIENT changes to %s " %self.tp)
				else:
					logger.info("[UPDATE] STILL INSUFFICIENT")
				return 
			elif self.tp == StringType.CONST:
				if self.val != val_str:
					self.tp = StringType.ENUM
					self.val = set([self.val, val_str])
					logger.info('[UPDATE] CONST to ENUM %s ' % str(self.val) )
				return
			elif self.tp == StringType.ENUM:
				if val_str not in self.val:
					logger.info('[UPDATE] ENUM add a member %s %s' % (str(self.val),str(val_str)) )
					self.val.add(val_str)
				return
			elif self.tp == StringType.NUMBER:
				if not stringIsNumeric(val_str):
					if isinstance(self.val, list):
						self.val.append(val_str)
						new_node = generateNodePattern(self.val)
						self.tp = new_node.tp
						self.val = new_node.val
					else:
						self.tp = StringType.CONST
						self.val = val_str
					logger.info('[UPDATE] NUMBER to %s ' % str(self.tp) )
				return				
			elif self.tp == StringType.QUOTED_NUMBER:
				if not stringIsNumeric(val_str[1:-1]):
					if isinstance(self.val, list):
						self.val.append(val_str)
						new_node = generateNodePattern(self.val)
						self.tp = new_node.tp
						self.val = new_node.val
					else:
						self.tp = StringType.CONST
						self.val = val_str
					logger.info('[UPDATE] QUOTED_NUMBER to %s ' % str(self.tp) )
				return	
			elif self.tp == StringType.URI:
				d_set = getDomainsFromString(val_str)
				self.val = self.val.union(d_set)
				logger.info('[UPDATE] updated URI DOMAIN SET to %s ' % str(self.val) )
				return
			elif self.tp == StringType.OTHER:
				if not self.val.check(val_str):
					self.val.update(val_str)
					return 
			return
		except Exception as e:
			logger.error('error in NodePattern.update: %s %s' %(val_str, str(e)))

	def loads(self, data_str):
		try:
			obj = json.loads(data_str)
		except Exception as e:
			displayErrorMsg('NodePattern.loads', str(e) + ' ' + str(data_str))
			return False

		if obj == None or obj['type'] == "ERROR":
			displayErrorMsg('NodePattern.loads', 'Object is invalid: ' + str(data_str))
			return False

		try:
			tp = StringTypeDict[obj['type']]
			self.tp = tp
			if tp == StringType.CONST:
				self.val = b64decode(obj['val'])
			elif tp == StringType.ENUM: 
				elems = obj['val'].split(',')
				decoded_vals = [b64decode(x) for x in elems]
				self.val = set(decoded_vals)
			elif tp == StringType.INSUFFICIENT: 
				elems = obj['val'].split(',')
				decoded_vals = [b64decode(x) for x in elems]
				self.val = decoded_vals
			elif tp == StringType.NUMBER:
				try:
					elems = obj['val'].split(',')
					if len(elems) == 1:
						self.val = ""
					else:
						decoded_vals = [b64decode(x) for x in elems]
						self.val = decoded_vals
				except Exception as e:
					displayErrorMsg('NodePattern.loads', 'error loading %s NUMBER %s' \
						%(obj['val'], str(e)) )
					self.val=""
			elif tp == StringType.QUOTED_NUMBER:
				try:
					elems = obj['val'].split(',')
					if len(elems) == 1:
						self.val = ""
					else:
						decoded_vals = [b64decode(x) for x in elems]
						self.val = decoded_vals
				except Exception as e:
					displayErrorMsg('NodePattern.loads', 'error loading %s QUOTED_NUMBER %s' \
						%(obj['val'], str(e)) )
					self.val=""
			elif tp == StringType.URI:
				elems = obj['val'].split(',')
				decoded_vals = [b64decode(x) for x in elems]
				self.val = set(decoded_vals)
			elif tp == StringType.OTHER:
				val = b64decode(obj['val'])
				val_obj = json.loads(val)
				patt = Pattern()
				patt.loads(val_obj)
				self.val = patt
			return True
		except Exception as e:
			displayErrorMsg("NodePattern.loads 2",str(e) + ' ' + str(data_str))
			return False

	def dumps(self):
		obj = {'type':'ERROR'}
		tp = self.tp
		# INSUFFICIENT:
		# val is the sample list
		# return {'type':'INSUFFICIENT', 'val': "decoded_sample1, decoded_sample2"}

		# CONST:
		# val is the const value
		# return {'type':'CONST', 'val':single_value}
		
		# ENUM:
		# val is the `set` of enum value
		# return {'type':'ENUM', 'val':"decoded_val1,decoded_val2"}
		
		# NUMBER/QUOTED_NUMBER:
		# val is ""
		# return {'type':'NUMBER', 'val':''} 
		
		# URI:
		# val is the `set` of domain value
		# return {'type':'URI', 'val':"decoded_domain1,decoded_domain2"}

		# OTHER:
		# val is Pattern object
		# return {'type':'OTHER', 'val':"decoded_pattern_string"}
		if tp == StringType.INSUFFICIENT:
			obj['type'] = "INSUFFICIENT"
			encoded_vals = [b64encode(x) for x in self.val]
			val = ','.join(encoded_vals)
			obj['val'] = val
		elif tp == StringType.CONST:
			obj['type'] = "CONST"
			obj['val'] = b64encode(str(self.val))
		elif tp == StringType.ENUM: 
			encoded_vals = [b64encode(x) for x in self.val]
			val = ','.join(encoded_vals)
			obj['type'] = "ENUM"
			obj['val'] = val
		elif tp == StringType.NUMBER:
			obj['type'] = "NUMBER"
			if isinstance(self.val, list):
				encoded_vals = [b64encode(x) for x in self.val]
				val = ','.join(encoded_vals)
				obj['val'] = val
			else:
				obj['val'] = ''
		elif tp == StringType.QUOTED_NUMBER:
			obj['type'] = "QUOTED_NUMBER"
			if isinstance(self.val, list):
				encoded_vals = [b64encode(x) for x in self.val]
				val = ','.join(encoded_vals)
				obj['val'] = val
			else:
				obj['val'] = ''
		elif tp == StringType.URI:
			encoded_vals = [b64encode(x) for x in self.val]
			val = ','.join(encoded_vals)
			obj['type'] = "URI"
			obj['val'] = val
		elif tp == StringType.OTHER:
			obj['type'] = "OTHER"
			obj['val'] = b64encode(self.val.dumps())

		return json.dumps(obj)

class Pattern():
	def __init__(self, fixed_len=-1,\
		min_len=-1, max_len=-1, prefix=None, alphanumeric=False, \
		special_char_set = None, domain_set = None):
		self.fixed_len = fixed_len
		self.min_len = min_len
		self.max_len = max_len
		self.prefix = prefix
		self.alphanumeric = alphanumeric
		self.special_char_set = special_char_set
		self.domain_set = domain_set

	def check(self, string):
		string = string.lower()
		if self.fixed_len != -1 and self.fixed_len != len(string):
			print "%s length is not correct" %string
			return False
		if self.min_len != -1 and len(string) < self.min_len:
			print "%s length is too short" %string
			return False
		if self.max_len != -1 and len(string) > self.max_len:
			print "%s length is too short" %string
			return False
		if self.prefix != None and (not string.startswith(self.prefix)):
			print "%s prefix is too correct" %string
			return False
		if self.alphanumeric and (not stringIsNumeric(string)):
			print "%s is not alphanumeric" %string
			return False
		if self.special_char_set != None and \
			(not (getSpecialCharacters(string) <= self.special_char_set)):
			print "%s contains not allowed characters" %string
			return False
		if self.domain_set != None and \
			(not (getDomainsFromString(string) <= self.domain_set)):
			print "%s contains not allowed domains" %string
			return False
		return True

	def update(self, string):
		try:
			string = string.lower()
			if self.fixed_len != -1 and self.fixed_len != len(string):
				self.fixed_len = -1
				logger.info("[UPDATE PATTERN] removed length req " )
			if self.min_len != -1 and len(string) < self.min_len:
				self.min_len = -1
				logger.info("[UPDATE PATTERN] removed min length req " )
			if self.max_len != -1 and len(string) > self.max_len:
				self.max_len = -1
				logger.info("[UPDATE PATTERN] removed max length req " )
			if self.prefix != None and (not string.startswith(self.prefix)):
				self.prefix = None
				logger.info("[UPDATE PATTERN] removed prefix req " )
			if self.alphanumeric and (not stringIsNumeric(string)):
				self.alphanumeric = None
				logger.info("[UPDATE PATTERN] removed alphanumeric " )
			if self.special_char_set != None and \
				(not (getSpecialCharacters(string) <= self.special_char_set)):
				s = getSpecialCharacters(string)
				self.special_char_set = self.special_char_set.union(s)
				logger.info("[UPDATE PATTERN] extended special_char_set " )
			if self.domain_set != None and \
				(not (getDomainsFromString(string) <= self.domain_set)):
				s = getDomainsFromString(string)
				self.domain_set.union(s)
				logger.info("[UPDATE PATTERN] extended domain set " )
		except Exception as e:
			logger.error('error in Pattern.update: %s %s ' %(string, str(e)))
		return

	def loads(self, obj):
		try:
			self.fixed_len = obj['fixed_len']
			self.min_len = obj['min_len']
			self.max_len = obj['max_len']
			self.prefix = obj['prefix']
			self.alphanumeric = obj['alphanumeric']
			if obj['special_char_set'] != None:
				self.special_char_set = set([b64decode(x) for x in obj['special_char_set']] )
			else:
				self.special_char_set = None
			if obj['domain_set'] != None:
				self.domain_set = set(obj['domain_set'])
			else:
				self.domain_set = None
		except Exception as e:
			print >> sys.stderr, "error in loading contents to pattern ", str(e)
			return False

	def debug(self):
		debug_str = "fixed_len:%d min_len:%d max_len:%d prefix:%s aln:%s char_set:%s d_set:%s" \
			%(self.fixed_len, self.min_len, self.max_len, \
				str(self.prefix), str(self.alphanumeric), str(self.special_char_set),str(self.domain_set) )
		return debug_str

	def dumps(self):
		try:
			obj = {'fixed_len' : -1, 'min_len' : -1, 'max_len' : -1, \
				'prefix' : None, 'alphanumeric': None, 'special_char_set': None, \
				'domain_set' : None}
			obj['fixed_len'] = self.fixed_len
			obj['min_len'] = self.min_len
			obj['max_len'] = self.max_len
			obj['prefix'] = self.prefix
			obj['alphanumeric'] = self.alphanumeric
			obj['special_char_set'] = [b64encode(x) for x in self.special_char_set]
			obj['domain_set'] = [x for x in self.domain_set]
			return json.dumps(obj)
		except Exception as e:
			print >> sys.stderr, "error in dumping contents ", str(e), self.debug()
			return json.dumps({'fixed_len' : -1, 'min_len' : -1, 'max_len' : -1, \
				'prefix' : None, 'alphanumeric': None, 'special_char_set': None, \
				'domain_set' : None})

	def __str__(self):
		return self.dumps()

'''
	Functions used for analyzing samples
'''
def generateNodePattern(sample_list):
	if len(sample_list) < MIN_SAMPLE_SIZE:
		print >>sys.stderr, "error: sample size too small: %d " %len(sample_list)
		return NodePattern(StringType.INSUFFICIENT, sample_list)

	size_of_sample = len(sample_list)

	# Test URI
	unquoted_sample_list = [urllib.unquote_plus(x) for x in sample_list]
 	domain_set = set()
 	url_count = 0
 	pattern = "http(s?)\:\/\/"
 	for item in unquoted_sample_list:
	 	try:
	 		item = item.lower()
	 		o = urlparse(item)
	 		scheme = o.scheme
	 		if scheme == "http" or scheme == "https":
	 			url_count += 1
 			cur_domains = getDomainsFromString(item)
 			domain_set = domain_set.union(cur_domains)
	 	except Exception as e:
	 		pass
	 		#print str(e)
	if url_count == len(unquoted_sample_list):
		return NodePattern(StringType.URI, domain_set)

	# Test NUMBER
	numeric_count = 0
	for item in sample_list:
		if stringIsNumeric(item):
			numeric_count += 1
	if numeric_count == len(sample_list):
		return NodePattern(StringType.NUMBER, sample_list)

	# Test QUOTED_NUMBER
	numeric_count = 0
	for item in sample_list:
		if stringIsNumeric(item[1:-1]) and \
			item[0] == item[-1] and \
			(item[0] == '"' or item[0] == "'"):
			numeric_count += 1
	if numeric_count == len(sample_list):
		return NodePattern(StringType.QUOTED_NUMBER, sample_list)

	# Test CONST
	sample_dict = {}
	for item in sample_list:
		item = item.lower().strip()
		if not item in sample_dict:
			sample_dict[item] = 1
		else:
			sample_dict[item] += 1

	if len(sample_dict) == 1:
		return NodePattern(StringType.CONST, sample_list[0])

  # Test ENUM
	percent = sorted(\
  	[float(sample_dict[k])/float(len(sample_list)) \
  		for k in sample_dict])
	if percent[0] > ENUM_THRESHOLD and size_of_sample >= 10:
		return NodePattern(StringType.ENUM, set(sample_dict.keys()))

	# fixed_len, min_len, max_len
	patt = Pattern(domain_set=domain_set)
	length_list = sorted([len(x) for x in sample_list])
	min_len = length_list[0]
	max_len = length_list[-1]
	if min_len == max_len:
		patt.fixed_len = min_len
	if max_len - min_len <= 2:
		patt.min_len = min_len
		patt.max_len = max_len

	# prefix
	sorted_list = sorted(sample_list)
	for i in range(min_len):
		if sorted_list[0][i] != sorted_list[-1][i]:
			break
	if i >= PATTERN_MIN_PREFIX:
		patt.prefix = sorted_list[0][:i]

	# special_char_set
	special_char_set = set()
	for item in sample_list:
		s = getSpecialCharacters(item)
		special_char_set = special_char_set.union(s)
	if len(special_char_set) > 0:
		patt.special_char_set = special_char_set

	return NodePattern(StringType.OTHER, patt)

'''
	Utilitity functions
'''
def getEffectiveDomainFromURL(url):
  try:
    o = tldextract.extract(url.lower())
    if o.domain == '':
    	return None
    return o.domain + '.' + o.suffix
  except Exception as e:
    print >> sys.stderr, "error in getting getEffectiveDomain ", str(e)
    return None

def getDomainsFromString(string):
	string = string.lower()
	pattern = re.compile("https?\:\/\/")
	pos = 0
	rs = set()
	try:
		while True:
			m = pattern.search(string, pos)
			if m == None:
				break
			domain = getEffectiveDomainFromURL(string[m.start():])
			rs.add(domain)
			pos = m.start() + 1
		return rs
	except Exception as e:
		print >> sys.stderr, "error in getDomainsFromString ", str(e)
		return set()

def stringIsNumeric(string):
	try:
		if string.isdigit():
			return True
		else:
			val = float(string)
			return True
	except:
		return False

def stringIsAlphanumericUnderscore(string):
	pattern = "^\w+$"
	try:
		m = re.match(pattern, string)
		return m != None
	except Exception as e:
		print >> sys.stderr, "error in stringIsAlphanumericUnderscore ", str(e)
		return False

def getSpecialCharacters(string):
	pattern = "\W"
	try:
		rs = re.findall(pattern, string)
	except Exception as e:
		print >> sys.stderr, "error in getSpecialCharacters ", str(e)
		return set()
	char_set = set(rs)
	return char_set


#analyzeStringListType(['YES','YES','NO','NO','NO','YES','NO','NO','NO','YES','NO']) 


