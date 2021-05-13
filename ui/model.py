from PySide2 import QtGui, QtCore
from tree import Tree
from tree.ui.delegate import TreeBranchItem, TreeValueItem, objRole

from tree.ui.lib import dropActionDict

class TreeModel(QtGui.QStandardItemModel):

	def __init__(self, tree, parent=None):
		super(TreeModel, self).__init__(parent)
		self.tree = None
		self.root = None
		self.setTree(tree)
		self.atRoot = False
		self.setHorizontalHeaderLabels(["branch", "value"])

	# drag and drop support
	def supportedDropActions(self):
		return QtCore.Qt.MoveAction

	def mimeTypes(self):
		""" use built in abstractTree serialisation to reduce
		entries to plain text, then regenerate them after """
		types = ["text/plain"]
		return types

	def mimeData(self, indices):
		# indices = indices[0::2]
		# filter only branchItems, not values
		indices = filter(lambda x: isinstance(
			self.itemFromIndex(x), TreeBranchItem), indices)
		infos = []
		for i in indices:
			branchItem = self.itemFromIndex(i)
			branch = branchItem.tree
			info = branch.serialise(includeAddress=True)
			infos.append(info)
		text = str(infos)
		mime = QtCore.QMimeData()
		mime.setText(text)
		return mime

	def dropMimeData(self, data, action, row, column, parentIndex):
		""" used for dropping and pasting """
		if action == QtCore.Qt.IgnoreAction:
			return True
		if not data.hasText():
			return False
		mimeText = data.text()
		infos = eval(mimeText)
		if not isinstance(infos, list):
			infos = [infos]

		for info in infos:
			tree = Tree.fromDict(info)

			# remove original entries
			if action == QtCore.Qt.MoveAction and "?ADDR" in info:
				found = self.tree.getBranch(info["?ADDR"])
				if found:
					found.remove()

			parentItem = self.itemFromIndex(parentIndex)
			if not parentItem:
				parentItem = self.invisibleRootItem()
				parentTree = self.tree.root
			else:
				parentTree = parentItem.tree
			parentTree.addChild(tree)

		self.sync()
		return True

	def branchFromIndex(self, index):
		""" returns tree object associated with qModelIndex """
		return self.itemFromIndex(index).tree

	def connectedIndices(self, index):
		""" return previous, next, upper and lower indices
		or None if not present
		only considers rows for now """
		result = {}
		nRows = self.rowCount(index.parent())
		nextIdx = index.sibling((index.row() + 1) % nRows, 0)
		result["next"] = nextIdx if nextIdx.isValid() else None
		prevIdx = index.sibling((index.row() - 1) % nRows, 0)
		result["prev"] = prevIdx if prevIdx.isValid() else None
		result["parent"] = index.parent() \
			if not index.parent() == QtCore.QModelIndex() else None
		return result

	@staticmethod
	def rowFromIndex(index):
		""" return the row index for either row or value index """
		return index.parent().child(index.row(), 0)

	def allRows(self, _parent=None):
		""" return flat list of all row indices """

		if _parent is None: _parent = QtCore.QModelIndex()
		rows = []

		for i in range(self.rowCount(_parent)):
			index = self.index(i, 0, _parent)
			rows.append(index)
			rows.extend(self.allRows(index))

		return rows

	def rowFromTree(self, tree):
		""" returns index corresponding to tree
		inelegant search for now """
		# print("row from tree {}".format(tree))
		for i in self.allRows():
			# print("found {}".format(self.treeFromRow(i)))
			if self.treeFromRow(i) == tree:
				# print("found match")
				return i

	def treeFromRow(self, row):
		""":rtype Tree """
		# return self.tree( self.data(row, objRole) )
		# print("treeFromRow {} {}".format(row, self.data(row, objRole)))
		return self.tree.getBranch(self.data(row, objRole))

	def duplicateRow(self, row):
		""" copies tree, increments its name, adds it as sibling
		:param row : QModelIndex for row """

		parent = row.parent()
		address = self.data(row, objRole)
		tree = self.tree(address)
		treeParent = tree.parent
		newTree = tree.fromDict(tree.serialise())
		newTree = treeParent.addChild(newTree)

		self.buildFromTree(newTree, parent=self.itemFromIndex(parent))

	def shiftRow(self, row, up=True):
		""" shifts row within its siblings up or down """
		tree = self.treeFromRow(row)
		parent = tree.parent
		if not parent: # shrug
			return
		startIndex = tree.index()
		newIndex = max(0, min(len(parent.branches), startIndex + (-1 if up else 1)))
		tree.setIndex(newIndex)
		# self.buildFromTree(parent=self.itemFromIndex(parent))
		parentIdx = self.rowFromTree(parent)
		self.itemsFromTree(parentItem=self.itemFromIndex(parentIdx))

	def deleteRow(self, row):
		""" removes tree branch, then removes item """

		tree = self.tree(self.data(row, objRole))
		tree.remove()

	def unParentRow(self, row):
		""" parent row to its parent's parent """
		branch = self.tree(self.data(row, objRole))
		parent = branch.parent
		if parent:
			grandparent = parent.parent
			if grandparent:
				branch.remove()
				#grandparent.addChild(branch)
				grandparent.addChild(branch, index=parent.index() + 1)

	def parentRows(self, rows, target):
		""" parent all selected rows to last select target """
		parent = self.tree(self.data(target, objRole))
		for i in rows:
			branch = self.tree(self.data(i, objRole))
			print("parent", parent)
			print("branch parent", branch.parent)
			if branch.parent is parent:
				print("branch parent is parent")
				continue
			branch.remove()
			parent.addChild(branch)

	def setTree(self, tree):
		self.tree = tree
		self.clear()
		self.root = TreeBranchItem(tree.root)
		rootRow = [self.root, TreeValueItem(tree)]

		self.appendRow(rootRow)

		for i in self.tree.branches:
			self.buildFromTree(i, parent=self.root)
		# self.endResetModel()
		self.setHorizontalHeaderLabels(["branch", "value"])

	def buildFromTree(self, tree=None, parent=None):
		"""
		rebuild subsection of tree
		:param tree : Tree
		:param parent : AbstractBranchItem below which to build"""
		branchItem = TreeBranchItem(tree=tree)
		textItem = TreeValueItem(tree)

		parent.appendRow([branchItem, textItem])
		for i in tree.branches:
			self.buildFromTree(i, parent=branchItem)
		self.itemChanged.emit(branchItem)
		return branchItem

	def itemsFromTree(self, parentItem=None,
	                  parentIndex=None, parentTree=None,
	                  ):
		""" rebuild items below parentItem """
		parentIndex = parentIndex or parentItem.index()
		parentTree = parentTree or parentItem.tree
		parentItem = parentItem or self.itemFromIndex(parentIndex)
		self.removeRows(0, self.rowCount(parentIndex), parentIndex)

		for i in parentTree.branches:
			branchItem = TreeBranchItem(i)
			valueItem = TreeValueItem(i)
			parentItem.appendRow([branchItem, valueItem])
			self.itemsFromTree(parentItem=branchItem)
		self.itemChanged.emit(parentItem)
		return parentItem

	def sync(self, *args, **kwargs):
		""" synchronises qt model from tree object,
		never directly other way round
		"""
		self.clear()
		self.setTree(self.tree)