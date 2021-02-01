
from __future__ import print_function
from PySide2 import QtCore, QtGui, QtWidgets
from functools import partial
from sys import version_info

if version_info[0] < 3: # hacky 2-3 compatibility
	pyTwo = True
	dict.items = dict.iteritems
	OrderedDict.items = OrderedDict.iteritems

else:
	pyTwo = False
	basestring = str

class PartialAction(QtWidgets.QAction):
	""" use partial as input to qt action """
	def __init__(self, fn, args=(), kwargs=None, name=None, parent=None):
		super(PartialAction, self).__init__(parent)
		kwargs = kwargs or {}
		self._partial = partial(fn, *args, **kwargs)
		self.triggered.connect(self._partial)
		self._name = None
		self.name = name or fn.__name__

	@property
	def name(self):
		return self.name
	@name.setter
	def name(self, val):
		self._name = val
		self.setText(val)

class ContextMenu(object):
	"""this is no reason this doesn't inherit from qmenu now,
	but it already works fine"""

	def __init__(self, view, title=None):
		self.view = view
		# self.rootMenu = menu or QtWidgets.QMenu("Take action:")
		self.rootMenu = QtWidgets.QMenu("Take action:", parent=self.view)
		if title: self.rootMenu.setTitle( title )

	def exec_(self, pos=None):
		"""allows smaller menus to return only the selected action
		for computation by outer code, or for a subclassed menu
		to be implemented with more thorough internal computation"""
		return self.rootMenu.exec_(pos)

	def addAction(self, fn=None, name=None, action=None, *args, **kwargs):
		""" given function or full PartialAction,
		add it to the menu """
		self.addSubAction(fn=fn, action=action, name=name, parent=self.rootMenu,
		                  args=args, kwargs=kwargs)

	# def addMenu(self, name):
	# 	menu = QtWidgets.QMenu(None, title=name)
	# 	self.rootMenu.addMenu(menu)
	# 	return ContextMenu(self.view, menu)

	# return menu

	def addMenu(self, name="", parent:QtCore.QObject=None):
		""" add new QMenu to given parent and return it"""
		menu = QtWidgets.QMenu(None, title=name)
		parent = parent or self.rootMenu
		parent.addMenu(menu)
		return menu


	def addSubAction(self, fn=None, name=None, action=None,
	                 args=(), kwargs=None,
	                 parent=None,

	                 ):
		"""add given PartialAction to the given object
		if you want a kwarg of 'parent', you need to
		pass an actual prebuilt action object
		"""

		if not parent: # add to this menu if none is given
			parent = self.rootMenu

		if not action:
			action = PartialAction(fn, parent=self.rootMenu,
			                       name=name,
				                   )
		parent.addAction(action)
		return action

	def marker(self):
		print ("TRIGGERING ACTION")

	def addCommand(self, name, func=None, shortcut=None, parent=None):
		if not parent:
			parent = self.rootMenu
		action = QtWidgets.QAction(name, self.view)
		# action.setShortcutVisibleInContextMenu(True)
		if shortcut:
			action.setShortcut(shortcut)
		if func:
			action.triggered.connect(func)
		parent.addAction(action, shortcut=shortcut)
		return action

	def addSeparator(self):
		self.rootMenu.addSeparator()

	def addSection(self, *args):
		self.rootMenu.addSection(*args)

	def buildMenusFromDict(self, menuDict=None):
		"""updates context menu with any action passed to it
		"""
		self.rootMenu.addSeparator()
		try:
			#print "context menuDict is {}".format(menuDict)
			self.buildMenu(menuDict=menuDict, parent=self.rootMenu)
		except RuntimeError("SOMETHING WENT WRONG WITH CONTEXT MENU"):
			pass

	"""CONTEXT MENU ACTIONS for allowing procedural function execution"""

	def buildMenu(self, menuDict=None, parent=None):
		"""builds menu recursively from keys in dict
		currently expects actionItems as leaves"""
		# print ""
		menuDict = menuDict or {}
		for k, v in menuDict.items():
			#print "k is {}, v is {}".format(k, v)
			if isinstance(v, dict):
				#print "buildMenu v is dict {}".format(v)
				if not v.keys():
				#	print "skipping"
					continue
				newParent = self.addMenu(name=k, parent=parent)
				self.buildMenu(v, parent=newParent)
			elif isinstance(v, list):
				#print "buildMenu v is list {}".format(v)
				for i in v:
					self.buildMenu(i, parent=parent)


	def buildMenusFromTree(self, tree, parent=None):
		""" builds recursively from tree
		only actions at leaves are considered """
		if tree.branches: # add menu for multiple actions
			parent = self.addMenu(name=tree.name, parent=parent)
			for branch in tree.branches:
				self.buildMenusFromTree(branch, parent)
			return parent
		else: # add single entry for single action
			action = self.addSubAction(tree.value, name=tree.name,
			                           parent=parent)

	def clearCustomEntries(self):
		"""clear only custom actions eventually -
		for now clear everything"""
		self.rootMenu.clear()


class KeyState(object):
	""" holds variables telling if shift, LMB etc are held down
	currently requires events to update, may not be a good idea to
	query continuously """

	class _BoolRef(object):
		""" wrapper for consistent references to bool value """
		def __init__(self, val):
			self._val = val
		def __call__(self, *args, **kwargs):
			self._val = args[0]
		def __str__(self):
			return str(self._val)
		def __nonzero__(self):
			return self._val.__nonzero__()


	def __init__(self):
		self.LMB = self._BoolRef(False)
		self.RMB = self._BoolRef(False)
		self.MMB = self._BoolRef(False)
		self.alt = self._BoolRef(False)
		self.ctrl = self._BoolRef(False)
		self.shift = self._BoolRef(False)

		self.mouseMap = {
			self.LMB : QtCore.Qt.LeftButton,
			self.RMB : QtCore.Qt.RightButton,
			self.MMB : QtCore.Qt.MiddleButton }

		self.keyMap = {
			self.alt: QtCore.Qt.AltModifier,
			# self.ctrl: QtCore.Qt.ShiftModifier, ### w h y ###
			# self.shift: QtCore.Qt.ControlModifier, ### w h y ###
			self.ctrl: QtCore.Qt.ControlModifier,
			self.shift: QtCore.Qt.ShiftModifier,
		}
		# shift and ctrl are swapped for me I kid you not

	def mousePressed(self, event):
		for button, v in self.mouseMap.items():
			button( event.button() == v)
		self.syncModifiers(event)

	def mouseReleased(self, event):
		for button, v in self.mouseMap.items():
			if event.button() == v:
				button(False)
		self.syncModifiers(event)

	def keyPressed(self, event):
		self.syncModifiers(event)

	def syncModifiers(self, event):
		""" test each individual permutation of keys
		against event
		this is ridiculous """
		# keys = self.keyMap.keys()
		# for sequence in itertools.combinations_with_replacement(
		# 		keys, len(keys)):
		# 	val = self.keyMap[sequence[0]]
		# 	for key in sequence[1:]: # same values should collapse to single
		# 		val = val | self.keyMap[key]
		# 	if event.modifiers() == val:
		# 		for key in sequence:
		# 			key(True)
		# 		return
		# 	for key in sequence:
		# 		key(False)

		for key, v in self.keyMap.items():
			key((event.modifiers() == v)) # not iterable
		if event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
			self.ctrl(True)
			self.shift(True)


	def debug(self):
		print(self.mouseMap)
		print(self.keyMap)
