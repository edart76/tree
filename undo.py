
""" optional module to allow undoing behaviour for edits to the tree
I'm aware this is very closely linked to the live inheritance system,
but I don't know how best to unite them
"""

from core import TreeBase

from functools import partial, wraps

class TreeUndoTracker(object):
	""" tracks deltas to a whole tree object from the root
	intended for use in uis rather than granular programs """

	@classmethod
	def muteSignals(cls, fn):
		@wraps(fn)
		def _wrapper(obj, *args, **kwargs):
			obj.tree.muteSignals()
			result = fn(*args, **kwargs)
			obj.tree.activateSignals()
			return result
		return _wrapper

	def __init__(self, treeRoot):
		self.tree = treeRoot

		self.undoStack = []
		self.redoStack = []

		self.tree.nameChanged.connect(self.doNameChange)
		self.tree.valueChanged.connect(self.doValueChange)
		self.tree.structureChanged.connect(self.doStructureChange)

	def doNameChange(self, branch, oldName, newName):
		self.undoStack.append({ "event" : "nameChange",
			"old" : oldName, "new" : newName, "branch" : branch})
		self.redoStack.clear()
	def doValueChange(self, branch, oldValue, newValue):
		""" try to copy old value object to set cleanly -
		otherwise we need recursive delta tracking """
		try:
			valType = type(oldValue)
			self.undoStack.append({"event" : "valueChange",
			                       "old" : valType(oldValue), "new" : newValue,
			                       "branch" : branch})
			self.redoStack.clear()
		except Exception as e:
			print("unable to copy simple value change for value {} - "
			      "is the value a complex object type?".format(oldValue))

	@muteSignals
	def undo(self):
		event = self.undoStack.pop(-1)

		b = event["branch"]
		if event["event"] == "nameChange":
			b.name = event["old"]
		elif event["event"] == "valueChange":
			b.value = event["old"]

		self.redoStack.append(event)

	@muteSignals
	def redo(self):
		event = self.redoStack.pop(-1)
		b = event["branch"]
		if event["event"] == "nameChange":
			b.name = event["new"]




