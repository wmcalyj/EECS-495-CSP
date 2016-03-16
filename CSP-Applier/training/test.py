from ASTAnalyzer import analyzeJSCodes
from ASTAnalyzer import analyzeJSCodesFinerBlock
from ASTAnalyzer import analyzeJSON
import sys
def readScript(path):
	script = open(path).read()
	return script

sc = readScript(sys.argv[1])
seqs, scripts = analyzeJSCodesFinerBlock(sc, False)
for index in range(len(seqs)):
	print "SCRIPT: %s" %scripts[index]
	tmp = [x.tag for x in seqs[index]]
	print "SEQ   : %s" %'_'.join(tmp)
	print ""
	#print tree.to_ecma()
