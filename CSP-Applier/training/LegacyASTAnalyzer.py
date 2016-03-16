class ASTOutputNode():
  def __init__(self, tag):
    self.tag = tag
    self.value = None
    self.child_num = 0

  def __eq__(self, other):
    if not isinstance(other, ASTOutputNode):
      return False
    return self.tag == other.tag

  def __ne__(self, other):
    return not self.__eq__(other)

class MyVisitor():
  def __init__(self, display=True):
    #only show class name and iterate children
    self.structure_class = set(["Block", "Node", \
      "FuncExpr", "FuncDecl", "This", "NewExpr", \
      ""])
    
    #leaf node and doesn't show value
    self.leaf_novalue_class = set(["Boolean", "Null", "Number", \
     "Regex"])

    #leaf node and show value
    self.leaf_value_class = set()

    self.node_order_list = []
    self.display = display
    self.identifier_map = {}
    self.first_level_seq = []
    #self.string_value_list = []

  
  def is_structure_class(self, node):
    name = node.__class__.__name__
    if name in self.structure_class:
      return True
    return False 

  def is_leaf_novalue_class(self, node):
    name = node.__class__.__name__
    if name in self.leaf_novalue_class:
      return True
    return False 
  
  def is_leaf_value_class(self, node):
    name = node.__class__.__name__
    if name in self.leaf_value_class:
      return True
    return False 

  def visit_sensitive_node(self, node, level):
    val = None
    if isinstance(node,ast.FunctionCall) or \
        isinstance(node, ast.NewExpr) or \
        isinstance(node, ast.ExprStatement):
        self.visit(node, level)
        val = "[FunctionCall||NewExpr]"
    elif isinstance(node, ast.Object):
      #for prop in child:
      #  left, right = prop.left, prop.right
      #   print "  object: left:%s, right:%s" %(left, right)
      count = 0
      val = {}
      for child in node:
        if isinstance(child, ast.Assign):
          key = self.visit_sensitive_node(child.left, level+1)
          value = self.visit_sensitive_node(child.right, level+1)
          if key != None and value != None:
            val[key] = value
        else:
          #print "    NO-ASSIGN-CHILD ",str(count),child, node
          if not "unknown" in val:
            val['unknown'] = child.__class__.__name__
          else:
            val['unknown'].append(child.__class__.__name__)
        count += 1
    elif isinstance(node, ast.Array):
      val = self.visit_sensitive_children(node, level)
    elif isinstance(node, ast.String):
      val = node.value
    elif isinstance(node, ast.Identifier):
      val = node.value

    return val

  def visit_sensitive_children(self, node, level):
    rs = []
    #print "DEBUG in processing visit_sensitive_children :NODE ",node
    for child in node:
      val = self.visit_sensitive_node(child, level+1)
      if val != None:
        rs.append(val)

    return rs

  def visit_Object(self, node, level):
    #self.display = True
    space = ' '.ljust(level*2)
    tag =  node.__class__.__name__
    index = len(self.node_order_list)
    if self.display:
      print "%s%s" %(space, tag)
    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)
    #print "process object ",node
    val = {}
    for child in node:
      if isinstance(child, ast.Assign):
        key = self.visit_sensitive_node(child.left, level+1)
        value = self.visit_sensitive_node(child.right, level+1)
        if key != None and value != None:
          val[key] = value
      else:
        #print "    NO-ASSIGN-CHILD ",str(count),child, node
        if not "unknown" in val:
          val['unknown'] = child.__class__.__name__
        else:
          val['unknown'].append(child.__class__.__name__)

    output_node.value = val
    output_node.child_num = \
      len(self.node_order_list) - no_child_len
    if level == 0:
      self.first_level_seq.append(copy.deepcopy(self.node_order_list[index:]) )
    #if self.display:
    #  print "%s%d]" %(space, output_node.child_num)
    return val

  def visit_Array(self, node, level):
    space = ' '.ljust(level*2)
    tag =  node.__class__.__name__
    if self.display:
      print "%s%s" %(space, tag)
    #print "Array with %d child " % (len(node.items))
    index = len(self.node_order_list)
    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)
    v = self.visit_sensitive_children(node, level+1)
    output_node.value = v
    output_node.child_num = \
      len(self.node_order_list) - no_child_len

    if level == 0:
      self.first_level_seq.append(copy.deepcopy(self.node_order_list[index:]))
    #print "display array: %d" %len(v)
    #for item in v:
    #  print item
    #print "done displaying array"

    #if self.display:
    #  print "%s%d]" %(space, output_node.child_num)
    return output_node
    
  def visit_String(self, node, level):
    space = ' '.ljust(level*2)
    tag =  node.__class__.__name__
    output_node = ASTOutputNode(tag)
    output_node.value = node.value
    output_node.child_num = 0
    self.node_order_list.append(output_node)
    #self.string_value_list.append(node.value)
    if self.display:
      print "%s%s [%s]" %(space, tag, node.value)
    return output_node.value
  
  def create_next_identifier(self):
    length = len(self.identifier_map)
    return "Var_%d" %length 

  def visit_Identifier(self, node, level):
    space = ' '.ljust(level*2)
    name = node.value
    if name in self.identifier_map:
      tag = self.identifier_map[name]
    else:
      tag = self.create_next_identifier()
      self.identifier_map[name] = tag

    output_node = ASTOutputNode(tag)
    output_node.value = node.value
    output_node.child_num = 0
    self.node_order_list.append(output_node)
    #self.string_value_list.append(node.value)
    if self.display:
      print "%s%s" %(space, tag)
    return node.value

  def visit_FunctionCall(self, node, level):
    space = ' '.ljust(level*2)
    #tag = node.__class__.__name__ 
    tag = node.__class__.__name__ 
    index = len(self.node_order_list)

    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)

    if self.display:
      print "%s%s" %(space, tag)
    #self.visit(node.identifier, level+1)
    rs = {'name':"FunCall", 'val':[]}
    for child in node:
      v = self.visit(child, level+1)
      if not v == None:
        rs['val'].append(v)
        
    output_node.child_num = \
      len(self.node_order_list) - no_child_len

    if level == 0:
      self.first_level_seq.append(copy.deepcopy(self.node_order_list[index:]))
    #if self.display:
    #  print "%s%d]" %(space, output_node.child_num)
    return rs

  def visit_VarStatement(self, node, level):
    #child_num = 0
    for child in node:
      tmp = self.visit(child, level+1)
      #child_num += tmp
    
    return None

  def visit_Program(self, node, level):
    #child_num = 0
    for child in node:
      tmp = self.visit(child, level)
      #child_num += tmp
    return None

  def leaf_value_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.value
    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    if self.display:
      print "%s%s" %(space, tag)
    output_node.child_num = 0
    return tag

  def leaf_novalue_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.__class__.__name__
    output_node = ASTOutputNode(tag)
    output_node.value = node.value
    output_node.child_num = 0
    self.node_order_list.append(output_node)

    if self.display:
      print "%s%s" %(space, tag)
    return tag

  def generic_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.__class__.__name__
    index = len(self.node_order_list)
    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)
      
    if self.display:
      print "%s%s" %(space, tag)
    rs = {'name':tag, 'val': []}
    for child in node:
      v = self.visit(child, level+1)
      #child_num += tmp
      if not v == None:
        rs['val'].append(v)
    #v = '_'.join(rs)
    output_node.child_num = \
      len(self.node_order_list) - no_child_len
    if level == 0:
      self.first_level_seq.append(copy.deepcopy(self.node_order_list[index:]))
    #if self.display:
    #  print "%s%d]" %(space, output_node.child_num)
    return rs

  def visit(self, node, level):
    if self.is_leaf_novalue_class(node):
      self.leaf_novalue_visit(node,level)
      return

    if self.is_leaf_value_class(node):
      self.leaf_value_visit(node,level)
      return

    method = 'visit_%s' % node.__class__.__name__
    return getattr(self, method, self.generic_visit)(node, level)