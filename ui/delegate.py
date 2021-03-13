from PySide2 import QtWidgets, QtGui, QtCore
from tree import Tree
from tree.ui.icons import doIcons, styleSheet, \
	squareCentre, squareDown, squareSides

# custom qt data roles
objRole = QtCore.Qt.UserRole + 1

rowHeight = 16


class AbstractBranchDelegate(QtWidgets.QStyledItemDelegate):
	""" use for support of locking entries, options on right click etc """

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


class TreeValueItem(QtGui.QStandardItem):
	"""overly specific but it's fine
	differentiate branch tag from actual value"""

	def __init__(self, tree):
		self.tree = tree
		self.trueType = type(self.tree.value)
		value = self.processValue(self.tree.value)

		super(TreeValueItem, self).__init__(value)

	def processValue(self, value):
		if value is None:
			return ""
		return str(value)

	def setData(self, value, *args, **kwargs):
		"""qt item objects manipulate trees directly, so
		anything already connected to the tree object signals
		works properly"""
		if self.trueType != type(value):
			self.trueType = type(value)
		self.tree.value = self.trueType(value)
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