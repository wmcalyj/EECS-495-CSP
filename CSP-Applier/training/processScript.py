import sys
from handler import extractAndStoreScriptsFromFileList

def main():
  extractAndStoreScriptsFromFileList(sys.argv[1])

if __name__ == "__main__":
  main()