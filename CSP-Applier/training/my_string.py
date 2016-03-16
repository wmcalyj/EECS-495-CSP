import sys, re,  distance,  editdistance
from urlparse import urlparse


def longest_common_substring(s1, s2):
	print "longest_common_substring"
	m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
	longest, x_longest = 0, 0
	for x in xrange(1, 1 + len(s1)):
		for y in xrange(1, 1 + len(s2)):
			if s1[x - 1] == s2[y - 1]:
				m[x][y] = m[x - 1][y - 1] + 1
				if m[x][y] > longest:
					longest = m[x][y]
					x_longest = x
			else:
				m[x][y] = 0
	return s1[x_longest - longest: x_longest]

def similar_strings(s1, s2, threthold):
	new_s1 = s1
	new_s2 = s2
	if len(s1) < len(s2):
		new_s1 = s1 + ' '.ljust(len(s2) - len(s1))
		new_s2 = s2
	elif len(s1) > len(s2):
		new_s2 = s2 + ' '.ljust(len(s1) - len(s2))
		new_s1 = s1
	length = len(new_s1)
	hamming = distance.hamming(new_s1,new_s2,normalized=True)
	print "hamming %f, threthold: %f" %(hamming, threthold)
	#if hamming >= threthold:
	#	return True

	print "calculating levenshtein ...length: %d vs %d " %(len(s1), len(s2))
	integer_threthold = 0
	if min(len(s1), len(s2)) > 15000:
		s1_arr = re.split('[;,]',s1)
		s2_arr = re.split('[;,]',s2)
		print "using fast levenshtein algorithm: s1-len:%d s2-len:%d" \
			%(len(s1_arr), len(s2_arr))
		levenshtein = editdistance.eval(s1_arr, s2_arr)
		integer_threthold = min(len(s1_arr), len(s2_arr)) * (1 - threthold)
	else:
		print "using standard levenshtein algorithm"
		levenshtein = editdistance.eval(s1, s2)
		integer_threthold = min(len(s1), len(s2)) * (1 - threthold)
	print "result levenshtein %d vs threthold %d " %(levenshtein,integer_threthold)
	if levenshtein <= integer_threthold:
		return True
	else:
		return False
	

	print "Done ",str(levenshtein)
	#jaccard = distance.jaccard(s1,s2)
	#print str(jaccard)
	
	'''
	levenshtein = distance.levenshtein(s1,s2)
	print "levenshtein %d, threthold:%d" %(levenshtein, int(length * threthold))
	if levenshtein < length - length * threthold:
		return True
	'''
	return False

def compare_two_string(str1, str2, threthold=0.8):
	if str1 == str2:
		return True
	whilespace = re.compile(r"\s+", re.MULTILINE)
	str1 = whilespace.sub('', str1.lower())
	str2 = whilespace.sub('', str2.lower())
	if str1 == str2:
		return True

	if len(str1) == 0 or len(str2) == 0:
		return False

	# Contain
	if str1 in str2 or str2 in str1:
		print "[INCLUDE: %s IN %s]" % (str1, str2)
		return True
	
	# Short string comparison
	if len(str1) <= 50 and len(str2) <= 50:
		return str1 == str2
	
	# Length difference larger than a threthold
	if abs(len(str1) - len(str2)) > min(len(str1), len(str2)) * 0.1 :
		return False

	# Longest string
	return similar_strings(str1, str2, threthold)

f = open(sys.argv[1])
contents = []
for line in f:
	contents.append(line.strip())
compare_two_string(contents[0],contents[1],0.8)
similar_strings(contents[0],contents[1],0.8)