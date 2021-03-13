""" pyside2 widget for editing tree objects """


from __future__ import print_function
from collections import OrderedDict
from PySide2 import QtCore, QtWidgets, QtGui
from main import Tree
from signal import Signal
#from delta import TreeDelta

from tree.ui.lib import KeyState, PartialAction, ContextMenu, SelectionModelContainer
# from tree.ui.style import style

from sys import version_info
import traceback, functools

from tree.ui.model import TreeModel
from tree.ui.delegate import AbstractBranchDelegate
from tree.ui.icons import doIcons, styleSheet, \
	squareCentre, squareDown, squareSides

pyTwo = version_info[0] < 3
if pyTwo:
	dict.items = dict.iteritems
	OrderedDict.items = OrderedDict.iteritems

# decorator for widget event methods to catch any exceptions
def catchAll(fn, logFunction=print):
	#print("catchAll fn {}".format(fn))
	@functools.wraps(fn)
	def inner(obj, *args, **kwargs):
		#print("inner obj {} args {} kwargs {}".format(obj, args, kwargs))
		try:
			return fn(obj, *args, **kwargs)
		except Exception as e:
			traceback.print_exc()
			logFunction(e)
	return inner



shrinkingPolicy = QtWidgets.QSizePolicy(
	QtWidgets.QSizePolicy.Minimum,
	QtWidgets.QSizePolicy.Minimum,
)

expandingPolicy = QtWidgets.QSizePolicy(
	QtWidgets.QSizePolicy.Expanding,
	QtWidgets.QSizePolicy.Expanding,
)



class WheelEventFilter(QtCore.QObject):
	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.Wheel:
			print("ate wheel event")
			return True
		else:
			return QtCore.QObject.eventFilter(self, obj, event)




def removeDuplicates( baseList ):
	existing = set()
	result = []
	for i in baseList:
		if i not in existing:
			result.append(i)
			existing.add(i)
	return result


class TreeWidget(QtWidgets.QTreeView):
	"""widget for viewing and editing an Tree
	display values in columns, branches in rows"""
	highlightKind = {
		"error": QtCore.Qt.red,
		"warning": QtCore.Qt.yellow,
		"success": QtCore.Qt.green,
	}
	background = QtGui.QColor(100, 100, 128)

	def __init__(self, parent=None, tree=None):
		""":param tree : Tree"""
		super(TreeWidget, self).__init__(parent)
		self.setSizePolicy(expandingPolicy)
		# self.installEventFilter(WheelEventFilter(self))
		if doIcons:
			self.setWindowIcon(QtGui.QIcon(squareCentre))
			self.setStyleSheet(styleSheet)

		self.setDragEnabled(True)
		self.setAcceptDrops(True)
		self.setDragDropMode(
			QtWidgets.QAbstractItemView.InternalMove
		)
		self.setSelectionMode(self.ExtendedSelection)
		self.setSelectionBehavior(self.SelectRows)
		#self.setDragDropMode()
		#self.setDropIndicatorShown()
		self.setAutoScroll(False)
		self.setFocusPolicy(QtCore.Qt.ClickFocus)
		self.setItemDelegate(AbstractBranchDelegate())
		self.menu = ContextMenu(self)

		self.sizeChanged = Signal()

		# convenience wrappers
		self.keyState = KeyState()

		self.highlights = {}  # dict of tree addresses to highlight
		self.tree = None
		self.root = None
		self.contentChanged = Signal()
		self.selectedEntry = None
		self.actions = {}
		self.modelObject = None

		# appearance
		header = self.header()
		header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		header.setStretchLastSection(True)
		self.savedSelectedTrees = []
		self.savedExpandedTrees = []

		self.setSizeAdjustPolicy(
			QtWidgets.QAbstractScrollArea.AdjustToContents
		)

		self.setUniformRowHeights(True)
		self.setIndentation(10)
		self.setAlternatingRowColors(True)
		self.showDropIndicator()

		self.initActions()

		if tree:
			tree = self.setTree(tree)
			self.resizeToTree()

		self.savedExpandedTrees = []
		self.savedSelectedTrees = []
		self.currentSelected = None
		self.editedIndex = None # stored on editing
		self.scrollPos = self.verticalScrollBar().value()

		self.contentChanged.connect(self.resizeToTree)
		self.expanded.connect(self.onExpanded)
		self.collapsed.connect(self.onCollapsed)

		self.expandAll()


	@property
	def sel(self):
		return SelectionModelContainer(self.selectionModel())

	def data(self, index, role=QtCore.Qt.DisplayRole):
		""" convenience """
		return self.model().data(index, role)

	def setTree(self, tree):
		"""associates widget with Tree object"""
		self.tree = tree
		self.root = tree.root

		self.modelObject = TreeModel(tree=self.tree)
		self.setModel(self.modelObject)
		self.setSelectionModel(QtCore.QItemSelectionModel(self.modelObject))
		self.modelObject.view = self

		self.modelObject.layoutAboutToBeChanged.connect(self.saveAppearance)
		self.modelObject.layoutChanged.connect(self.restoreAppearance)
		self.expandAll()
		self.setRootIndex(self.model().invisibleRootItem().child(0, 0).index())

		return self.modelObject

	def initActions(self):
		"""sets up copy, add, delete etc actions for branch entries"""

	# region events

	@catchAll
	def mousePressEvent(self, event):
		self.keyState.mousePressed(event)

		# only pass event on editing,
		# need to manage selection separately
		if not (self.keyState.ctrl or self.keyState.shift)\
				or event.button() == QtCore.Qt.RightButton:
			return super(TreeWidget, self).mousePressEvent(event)

		index = self.indexAt(event.pos())
		self.onClicked(index)

	def onClicked(self, index):
		""" manage selection manually """
		# if ctrl, toggle selection
		if self.keyState.ctrl and not self.keyState.shift:
			self.sel.toggle(index)
			self.sel.setCurrent(index)
			return
		elif self.keyState.shift: # contiguous span

			clickRow = self.model().rowFromIndex(index)
			currentRow = self.model().rowFromIndex(
				self.sel.current())
			# find physically lowest on screen
			if self.visualRect(clickRow).y() < \
				self.visualRect(currentRow).y():
				fn = self.indexAbove
			else:
				lowest = clickRow
				highest = currentRow
				fn = self.indexBelow
			targets = []
			selStatuses = []
			checkIdx = currentRow
			selRows = self.selectionModel().selectedRows()
			count = 0
			while checkIdx != clickRow and count < 4:
				count += 1
				checkIdx = fn(checkIdx)
				targets.append(checkIdx)
				selStatuses.append(checkIdx in selRows)

			addOrRemove = sum(selStatuses) < len(selStatuses) / 2
			for row in targets:
				self.sel.add(row)

		# set previous selection
		self.sel.setCurrent(index)
		self.currentSelected = index

	def contextMenuEvent(self, event):

		self.makeMenu()
		# pos = event.localPos()
		pos = event.globalPos()
		pos = event.pos()
		# pos = self.viewport().mapFromGlobal( self.mapToGlobal( event.pos()))
		pos = self.mapToGlobal(event.pos())
		menu = self.menu.exec_(pos)

	def makeMenu(self):
		""" create context menu """
		self.menu.clearCustomEntries()
		# check for tree options
		addSep = 0
		for i in self.selectionModel().selectedRows():
			branch = self.modelObject.treeFromRow(i)
			for option in branch.extras.get("options") or []:
				if not addSep: self.menu.addSection("Tree options")
				self.menu.addAction(
					PartialAction(fn=Tree._setTreeValue,
					              parent=None,
					              name=option,
					              args=[branch, option])
				)
				addSep = 1
		if addSep: self.menu.addSeparator()
		self.menu.addAction(fn=self.copyEntries)
		self.menu.addAction(fn=self.pasteEntries)
		self.menu.addAction(fn=self.display)
		return self.menu

	def copyEntries(self):
		clip = QtGui.QGuiApplication.clipboard()
		indices = self.selectionModel().selectedRows()  # i hate
		# print "indices {}".format(indices)
		if not indices:
			print("no entries selected to copy")
			return
		#index = indices[0]  # only copying single entry for now
		mime = self.model().mimeData(indices)
		print( "copy mime {}".format(mime.text()))
		clip.setMimeData(mime)
		"""get mime of all selected objects
		set to clipboard
		"""

	def pasteEntries(self):
		print("pasting")
		indices = self.selectedIndexes()  # i strongly hate
		if not indices:
			return
		index = indices[0]
		clip = QtGui.QGuiApplication.clipboard()
		data = clip.mimeData()
		print("mime is {}".format(data.text()))
		self.model().dropMimeData(data,
		                          QtCore.Qt.CopyAction,
		                          index.row(),
		                          index.column(),
		                          index.parent())
		# if not data:
		# 	print("no data to regenerate")
		# 	return
		# try:
		# 	regenDict = eval(data.text())
		# except:
		# 	print("unable to decode {}".format(data.text()))
		# 	return
		#
		# pasteTree = Tree.fromDict(regenDict)
		#
		# # get parent item of selected index, addChild with abstract tree,
		# commonParentIndex = index
		# commonParentItem = self.model().itemFromIndex(commonParentIndex) \
		#                    or self.model().invisibleRootItem()
		#
		# commonParentItem.tree.addChild(pasteTree)
		# self.model().buildFromTree(pasteTree, commonParentItem)
		# pass


	def dragEnterEvent(self, event):
		return super(TreeWidget, self).dragEnterEvent(event)
		# event.accept()

	def dragMoveEvent(self, event):
		return super(TreeWidget, self).dragMoveEvent(event)
		# event.accept()

	def keyPressEvent(self, event):
		""" bulk of navigation operations,
		for hierarchy navigation aim to emulate maya outliner

		ctrl+D - duplicate
		del - delete

		left/right - select siblings
		up / down - select child / parent

		p - parent selected branches to last selected
		shiftP - parent selected branches to root

		ctrl + shift + left / right - shuffle selected among siblings

		events modify the core tree data structure - model and view
		are rebuilt atop it
		not sure if there is an elegant way to structure this
		going with battery of if statements

		"""
		self.keyState.keyPressed(event)

		sel = self.selectionModel().selectedRows()
		key = event.key()
		# don't override anything if editing is in progress
		if self.state() == QtWidgets.QTreeView.EditingState or len(sel) == 0:
			#return super(TreeWidget, self).keyPressEvent(event)
			return True

		# editing entry
		if key in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:

			# shift-enter begins editing on value
			if self.keyState.shift:
				idx = sel[0].siblingAtColumn(1)
			else: # edit name
				idx = sel[0]
			self.editedIndex = idx
			self.edit(idx)
			return True

		if self.keyState.ctrl and key in \
			(QtCore.Qt.Key_D, QtCore.Qt.Key_C, QtCore.Qt.Key_V):
			if key == QtCore.Qt.Key_D:  # duplicate
				for row in sel:
					self.modelObject.duplicateRow(row)
			elif key == QtCore.Qt.Key_C:  # copy
				for row in sel:
					self.copyEntries()
			elif key == QtCore.Qt.Key_V:  # paste
				for row in sel:
					self.pasteEntries()

		# shifting row up or down
		if self.keyState.shift and self.keyState.ctrl:
			self.saveAppearance()
			if key in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Left]:
				for row in sel:
					self.modelObject.shiftRow(row, up=True)
			elif key in [QtCore.Qt.Key_Down, QtCore.Qt.Key_Right]:
				for row in sel:
					self.modelObject.shiftRow(row, up=False)
			self.restoreAppearance()
			return True

		# deleting
		if key == QtCore.Qt.Key_Delete:
			for row in sel:
				self.modelObject.deleteRow(row)
				return True

		# reparenting
		if key == QtCore.Qt.Key_P:
			if self.keyState.shift:
				for row in sel:  # unparent row
					self.model().unParentRow(row)
			elif len(sel) > 1:  # parent
				self.model().parentRows(sel[:-1], sel[-1])
			return True
		if key in (QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab):
			#print(self.keyState.shift)
			if self.keyState.shift: # unparent row
				print(sel)
				for row in sel:
					self.model().unParentRow(row)
			else: # parent to row directly above
				for row in reversed(sel):
					adj = self.model().connectedIndices(row)
					if adj["prev"] and not adj["prev"] == row:
						self.model().parentRows([row], target=adj["prev"])
			self.sync()
			return True

		# direction keys to move cursor
		if key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right,
			QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
			self.sel.clear()
			if self.sel.current():
				sel.append(self.sel.current())
			for i in sel:
				adj = self.model().connectedIndices(i)
				target = None
				if key == QtCore.Qt.Key_Left:
					# back one index
					if adj["prev"]:
						target = adj["prev"]
				elif key == QtCore.Qt.Key_Right:
					# forwards one index
					if adj["next"]:
						target = adj["next"]
				elif key == QtCore.Qt.Key_Up:
					# up to parent
					if adj["parent"]:
						target = (i.parent())
					else: target = i
				# elif key == QtCore.Qt.Key_Down:
				else:
					# down to child
					if i.child(0, 0).isValid():
						target = i.child(0,0)
					else: target = i

				if target:
					self.sel.add(target)
				if i == self.sel.current():
					self.sel.setCurrent(target)

			return True

		return super(TreeWidget, self).keyPressEvent(event)


	#endregion

	# region appearance
	def resizeToTree(self, *args, **kwargs):
		self.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)
		# get rough idea of how long max tree entry is
		maxLen = 0
		for k, v in self.tree.iterBranches():
			maxLen = max(maxLen, len(k) + len(str(v.value)))

		self.resize(self.viewportSizeHint().width(),
		            self.viewportSizeHint().height() +
		            self.header().rect().height())
		self.sizeChanged()
		pass

	def saveAppearance(self):
		""" saves expansion and selection state """
		# print("saving appearance")
		self.savedSelectedTrees = []
		self.savedExpandedTrees = []
		self.currentSelected = None
		for i in self.selectionModel().selectedRows():
			branch = self.modelObject.treeFromRow(i)
			self.savedSelectedTrees.append(branch)
		# print("allrows {}".format(self.modelObject.allRows()))
		for i in self.modelObject.allRows():
			if not self.model().checkIndex(i):
				print("index {} is not valid, skipping".format(i))
			# print("treeFromRow {}".format(self.modelObject.treeFromRow(i)))
			if self.isExpanded(i):
				# print()
				#try:
				branch = self.modelObject.treeFromRow(i)
				# except:
				# 	branch = None
				if branch:
					self.savedExpandedTrees.append(branch)
		if self.selectionModel().currentIndex().isValid():
			self.currentSelected = self.model().treeFromRow(
				self.selectionModel().currentIndex() )
			# self.currentSelected = self.sel.current()
		# save viewport scroll position
		self.scrollPos = self.verticalScrollBar().value()

	def restoreAppearance(self):
		""" restores expansion and selection state """
		self.setRootIndex(self.model().invisibleRootItem().child(0, 0).index())
		self.resizeToTree()

		for i in self.savedSelectedTrees:
			if not self.model().rowFromTree(i):
				continue

			self.selectionModel().select(
				self.model().rowFromTree(i),
				QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows
			)
		for i in self.savedExpandedTrees:
			if not self.model().rowFromTree(i):
				continue
			self.expand( self.modelObject.rowFromTree(i) )
			pass
		if self.currentSelected:
			#print("setting current")
			row = self.modelObject.rowFromTree(self.currentSelected)
			self.sel.setCurrent(row)
		self.verticalScrollBar().setValue(self.scrollPos)

	def sync(self, *args, **kwargs):
		self.saveAppearance()
		sel = self.selectionModel()
		self.model().sync()
		self.setRootIndex(self.model().invisibleRootItem().child(0, 0).index())
		self.setSelectionModel(sel)
		self.restoreAppearance()
		self.expandAll()
		self.resizeToTree()

	def addHighlight(self, address, kind):
		"""adds a highlight to TreeView line, depending on reason"""
		colour = QtCore.QColor(self.highlightKind[kind])
		self.highlights[address] = kind

	def _recursiveApply(self, fn, startIndex, callSuper=True,
	                    ):
		if callSuper:
			result = super(TreeWidget, self).fn(startIndex)
		else: result = None
		for i in range(self.model().rowCount(startIndex)):
			childIdx = startIndex.child(i, 0)
			fn(childIdx)
		return result

	def onExpanded(self, index):
		""" check for shift - recursively expand children if so """
		if self.keyState.shift:
			self._recursiveApply(self.expand, index)
	def onCollapsed(self, index):
		""" check for shift - recursively expand children if so """
		if self.keyState.shift:
			self._recursiveApply(self.collapse, index)



	def display(self):
		print(self.tree.display())
	#endregion

	#
	# def commitData(self, editor):
	# 	print("commit", self.editedIndex)
	# 	# if self.editedIndex:
	# 	# 	#print(self.editedIndex.isValid())
	# 	# 	self.sel.setCurrent(self.editedIndex)
	# 	# 	self.sel.add(self.editedIndex)
	# 	return super(TreeWidget, self).commitData(editor)
	# 	# if self.editedIndex:
	# 	# 	print(self.editedIndex.isValid())
	# 	# 	self.sel.setCurrent(self.editedIndex)
	# 	# 	self.sel.add(self.editedIndex)

	def select(self, branch=None, path=None, clear=True):
		""" main user selection method """
		if clear:
			self.sel.clear()
		if not (branch or path): # select -cl 1
			return
		if path:
			result = self.tree.getBranch(path )
			if result is None:
				return None
			branch = [result]
		else:
			if not isinstance(branch, (list, tuple)):
				branch = branch

		for b in branch:
			item = self.model().rowFromTree(b)
			self.sel.add(item.index())

	def focusNextPrevChild(self, direction):
		return False


class EditTree(QtWidgets.QUndoCommand):

	def __init__(self, tree):
		newData = None
		prevData = None
		pass

	def redo(self):
		""" set tree from new data """

	def undo(self):
		""" set tree from prev data """


def test():

	from tree.test_tree import midTree
	import sys
	app = QtWidgets.QApplication(sys.argv)
	win = QtWidgets.QMainWindow()

	#winLayout = QtWidgets.QVBoxLayout()

	widg = TreeWidget(win, tree=midTree)
	#winLayout.addWidget(widg)
	# winLayout.setSpacing(0)
	# winLayout.setContentsMargins(0, 0, 0, 0)

	#win.setLayout(winLayout)
	win.setCentralWidget(widg)
	win.show()
	sys.exit(app.exec_())





if __name__ == "__main__":
	w = test()
	w.show()
	# test the tree widget
	# from PySide2 import QtCore
	# from tree.test_tree import tempTree
	# import sys
	# app = QtWidgets.QApplication(sys.argv)
	# win = QtWidgets.QMainWindow()
	#
	# #winLayout = QtWidgets.QGridLayout(win)
	#
	# widg = TreeWidget(win, tree=tempTree)
	# #winLayout.addWidget(widg)
	# # winLayout.setSpacing(0)
	# # winLayout.setContentsMargins(0, 0, 0, 0)
	#
	#
	# #win.setLayout(winLayout)
	# win.setCentralWidget(widg)
	# s = win.show()
	# #app.exec_()
	# sys.exit(app.exec_())
	#
	# print(s)

