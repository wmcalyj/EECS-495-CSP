import os, sys, re

dir_name = sys.argv[1]
dst_dir_name = sys.argv[2]
files = os.listdir(dir_name)
name_pattern = "\d+_(.+)"
url_pattern = "http(.)+?\|\|"

for fname in files:
  m = re.match(name_pattern, fname)
  if m == None:
    continue
  new_f_name = m.group(1)
  
  full_name = os.path.join(dir_name, fname)
  f = open(full_name)
  contents = ""
  for line in f:
    if line.startswith("start analyzeing values"):
      break
    new_line = re.sub(url_pattern, '', line)
    if contents == "":
      contents += new_line
    elif len(new_line) != len(line):
      break
    else:
      contents += new_line
  if len(contents) == "":
    print "error extracing script"
    continue
  f.close()
  
  fw = open(os.path.join(dst_dir_name,new_f_name),'w')
  fw.write(contents)
  fw.close()
