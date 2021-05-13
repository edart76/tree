
import ast, json, re
from six import string_types, iteritems
from pprint import pprint

from PySide2 import QtWidgets, QtGui, QtCore
from tree import Tree
from tree.ui.icons import doIcons, styleSheet, \
	squareCentre, squareDown, squareSides

# custom qt data roles
objRole = QtCore.Qt.UserRole + 1

rowHeight = 16

class TreeBranchItem(QtGui.QStandardItem):
	"""small wrapper allowing standardItems to take tree objects directly"""
	if doIcons:
		ICONS = {"centre": QtGui.QIcon(squareCentre),
		         "down": QtGui.QIcon(squareSides["down"])}

	def __init__(self, tree):
		""":param tree : Tree"""
		self.tree = tree or Tree("root")
		super(TreeBranchItem, self).__init__(self.tree.name)
		# super(AbstractBranchItem, self).setIcon(self.ICONS["centre"])

		self.treeType = Tree  # add support here for subclasses if necessary
		self.setColumnCount(1)
		# self.icon = self.ICONS["centre"]

		self.trueType = type(self.tree.name)

	def data(self, role=QtCore.Qt.DisplayRole):
		""" just return branch name
		data is used when regenerating abstractTree from model"""

		# if role == QtCore.Qt.DecorationRole:
		# 	return self.icon
		if role == objRole:
			# return self.tree # crashes
			return self.tree.address
		elif role == QtCore.Qt.SizeHintRole:
			return QtCore.QSize(
				len(self.tree.name) * 7.5,
				rowHeight)

		base = super(TreeBranchItem, self).data(role)
		return base

	def setData(self, value, role):  # sets the NAME of the tree
		name = self.tree._setName(value)  # role is irrelevant
		self.emitDataChanged()
		return super(TreeBranchItem, self).setData(name, role)


	def parents(self):
		""" returns chain of branch items to root """
		if self.parent():
			return [self.parent()] + self.parent().parents()
		return []

	# def clone(self):
	# 	""" return new key : value row """
	# 	newBranch = self.treeType.fromDict( self.tree.serialise )

	def __repr__(self):
		return "<BranchItem {}>".format(self.data())


"""
quoteless functions for stringifying lists and dicts
the elegant way to do this is wtih AST, but without
ast.unparse(), which is new, this only works
one way - trashy string functions used to remove quotes
"""

literalTypes = (
	bool, int, float,
)

# regex checking for scientific notation
sciNotationReg = r"^[+\-]?(?=\.\d|\d)(?:0|[1-9]\d*)?(?:\.\d*)?(?:\d[eE][+\-]?\d+)?$"

# test = "3.4e10"
# pattern = re.compile(sciNotationReg)
# result = re.findall(pattern, test)
# print(result)
# test = ".e"
# result = re.findall(pattern, test)
# print(result)

def quotelessFn(value):
	if isinstance(value, dict):
		return mapToQuotelessStr
	elif hasattr(value, "__iter__") and not\
		isinstance(value, string_types):
		return seqToQuotelessStr
	return None

def seqToQuotelessStr(seq):
	""" given sequence, return a string of it
	with all internal string quotes removed """
	tokens = [] # individual quoteless tokens
	print(seq)
	for item in seq:
		if isinstance(item, literalTypes):
			tokens.append(str(item))
			continue
		if quotelessFn(item):
			item = quotelessFn(item)(item)
		# check for escaped \"
		if item[0:1] == "\\\'" and item [-2:] == "\\\'":
			item = "\"" + item[2:-2] + "\""
		tokens.append(str(item))
	sep = ", "
	resultStr = "[ " + sep.join(tokens) + " ]"
	return resultStr

def mapToQuotelessStr(inMap):
	""" given sequence, return a string of it
	with all internal string quotes removed """
	tokens = []
	for k, v in iteritems(inMap):
		tie = []
		for item in (k, v):
			if quotelessFn(item):
				item = quotelessFn(item)(item)
			tie.append(str(item))
		tieSep = " : "
		tokens.append(tieSep.join(tie))
	sep = ", "
	resultStr = "{ " + sep.join(tokens) + " }"
	return resultStr




class ASTNameToConstant(ast.NodeTransformer):
	""" walks tree, turning all found Name
	nodes to Constants
	aka puts quotes around raw names """
	def __init__(self, scopeVars=None):
		""" scopeVars used to whitelist any actual
		correct names """
		super(ASTNameToConstant, self).__init__()
		self.scopeVars = scopeVars or []

	def visit_Name(self, node):
		""" convert Name node to Constant of its value """
		constant = ast.Constant(value=node.id)
		return constant

class ASTConstantToName(ast.NodeTransformer):
	""" walks tree, turning all found Constant
	nodes to Names
	aka removes quotes from strings """
	def __init__(self, scopeVars=None, varPrefix="$"):
		""" scopeVars used to whitelist any actual
		correct names
		to identify them the varPrefix will be prepended
		to displayed name - not recommended """
		super(ASTConstantToName, self).__init__()
		self.scopeVars = scopeVars or []
		self.varPrefix = varPrefix

	def visit_Constant(self, node):
		""" convert Constant node to Name of its value """
		name = ast.Name(id=node.value)
		return name

def objToQuoteless(obj):
	tree = ast.parse(str(obj), mode="eval")
	result = ast.fix_missing_locations(
		ASTConstantToName().visit(tree)	)
	result = ast.unparse(result) # new in py 3.9 :(
	return result

def quotelessToObj(value=""):
	""" given quoteless string, return string, dict or obj """
	value = value.rstrip()
	# check for sci notation
	if re.findall(sciNotationReg, value):
		print("sci found", value)
		return value

	try:
		result = ast.parse(value, mode="eval")
	except: # for simple unquoted strings this fails
		result = value
		return value

	result = ast.fix_missing_locations(
		ASTNameToConstant().visit(result)
	)

	result = ast.literal_eval(result)
	return result

class TreeValueItem(QtGui.QStandardItem):
	"""overly specific but it's fine
	differentiate branch tag from actual value"""

	def __init__(self, tree):
		self.tree = tree
		self.trueType = type(self.tree.value)
		value = self.processValue(self.tree.value)
		#value = tree.value

		super(TreeValueItem, self).__init__(value)

	def processValue(self, value):
		""" strip inner quotes from container values -
		this is the raw data, separate from any fancy rendering later
		"""
		if value is None:
			return ""
		if quotelessFn(value):
			value = quotelessFn(value)(value)
		# value = objToQuoteless(value) # doesn't work the other way round
		return str(value)

	def setData(self, value, *args, **kwargs):
		"""qt item objects manipulate trees directly, so
		anything already connected to the tree object signals
		works properly"""

		valueObj = quotelessToObj(value)

		self.tree.value = valueObj
		super(TreeValueItem, self).setData(value, *args, **kwargs)

	def data(self, role=QtCore.Qt.DisplayRole):
		if role == QtCore.Qt.SizeHintRole:
			return QtCore.QSize(
				len(str(self.tree.value)) * 7.5 + 3,
				rowHeight)
		base = super(TreeValueItem, self).data(role)
		return base

	def rowCount(self):
		return 0

	def columnCount(self):
		return 0

	def column(self):
		return 1

	def __repr__(self):
		return "<ValueItem {}>".format(self.data())


class TreeNameDelegate(QtWidgets.QStyledItemDelegate):
	""" use for support of locking entries, options on right click etc
	could also be used for drawing proxy information

	"""

	# def createEditor(self, parent, options, index):
	# 	""" check for options or if entry is locked """
	# 	index = index or self.index()
	# 	item = index.model().itemFromIndex(index)
	# 	if isinstance(item, AbstractBranchItem):
	# 		# don't mess with moving / renaming branches
	# 		return super(AbstractBranchDelegate, self).createEditor(parent, options, index)
	# 	branch = item.tree
	# 	if branch.extras.get("lock") or "options" in branch.extras:
	# 		return None
	# 	return super(AbstractBranchDelegate, self).createEditor(parent, options, index)

class TreeValueDelegate(QtWidgets.QStyledItemDelegate):
	""" used to display more complex processing of value items """

	def displayText(self, value, locale):
		""" format to remove quotes from strings, lists and dicts """
		#print("delegate called for {}".format(value))
		return value

