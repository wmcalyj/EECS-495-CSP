import os, sys, re, base64
from base64 import b64encode
from base64 import b64decode
import strings


def processStringLine(line):
	pattern = '^string\d+\:(.+)$'
	m = re.match(pattern, line)
	if m == None:
		print "error in processing string: ",line
		return None
	values = m.group(1).strip().split(',')
	decoded_values = [b64decode(x) for x in values]
	return decoded_values

def processObject(line):
	pattern = '^object\d+\: (.+)\:(.+)$'
	m = re.match(pattern, line)
	if m == None:
		print "error in processing object: ",line
		return None
	key = m.group(1).strip()
	values = m.group(2).strip().split(',')
	decoded_values = [b64decode(x) for x in values]
	return key, decoded_values

def processArray(line):
	pattern = '^array\d+\: (.+)\:(.+)$'
	m = re.match(pattern, line)
	if m == None:
		print "error in processing object: ",line
		return None
	key = m.group(1).strip()
	values = m.group(2).strip().split(',')
	decoded_values = [b64decode(x) for x in values]
	return key, decoded_values

def displayTypeAndPattern(tp, data):
	if tp == strings.StringType.CONST:
		return "[%s][ ] " %("CONST")
	elif tp == strings.StringType.ENUM:
		keys = ','.join(data.keys())
		return "[%s][%s] " %("ENUM", keys)
	elif tp == strings.StringType.NUMBER:
		return "[%s][ ] " %("NUMBER")
	elif tp == strings.StringType.QUOTED_NUMBER:
		return "[%s][ ] " %("QUOTED_NUMBER")
	elif tp == strings.StringType.URI:
		return "[%s][%s] " %("URI", ','.join(data))
	elif tp == strings.StringType.OTHER:
		return "[%s][%s] " %("OTHER", data.dumps())
	else:
		return "[ERROR:%s]" %tp

dirname = sys.argv[1]
files = os.listdir(dirname)
for file_name in files:
	#print file_name
	f = open(os.path.join(dirname, file_name))
	begin = False
	for line in f:
		line = line.strip()
		if line.startswith('start analyzeing values'):
			begin = True
			continue
		if not begin:
			continue
		if line.startswith('string'):
			vals = processStringLine(line)
			tp, data = strings.analyzeStringListType(vals)
			tmp1 = ','.join(vals)
			tmp2 = displayTypeAndPattern(tp, data)
			print "STRING: %s [%s]" %(tmp2, tmp1)

		elif line.startswith('object'):
			key, vals = processObject(line)
			displayTypeAndPattern(tp, data)
			tp, data = strings.analyzeStringListType(vals)
			tmp1 = ','.join(vals)
			tmp2 = displayTypeAndPattern(tp, data)
			print "OBJECT %s: %s [%s]" %(key, tmp2, tmp1)
			#print "KEY:%s VAL:" %key,
			#for val in vals:
			#	print val,
			#print ''
		elif line.startswith('array'):
			key, vals = processArray(line)
			tp, data = strings.analyzeStringListType(vals)
			tmp1 = ','.join(vals)
			tmp2 = displayTypeAndPattern(tp, data)
			print "ARRAY %s: %s [%s]" %(key, tmp2, tmp1)
