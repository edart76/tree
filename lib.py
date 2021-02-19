
""" python functions used in tree and associated objects"""
from __future__ import print_function
import importlib
import string, difflib
from collections import deque, namedtuple
import sys, os
from sys import version_info

import inspect


if version_info[0] < 3: # hacky 2-3 compatibility
	pyTwo = True
	basestring = str
else:
	pyTwo = False


class DiffUndo(object):
	""" maintain undo records based on serialised
	object data
	we assume that any object using this contains only simple datatypes

	At the moment there is no benefit to using difflib -
	redo this later saving opcodes and only diffed stretches
	"""

	diffKeys = [
		"replaceIndex", "replaceData",
		"deleteIndices", # tuple of (start, end)
		"insertIndex", "insertData"
	]
	replaceData = namedtuple("replaceData", ["start", "end", "data"])
	insertData = namedtuple("insertData", ["index", "data"])
	deleteData = namedtuple("deleteData", ["start", "end", "data"])

	def __init__(self, baseSeq="", fromStringFn=None):
		""" only works properly on strings for now
		:param baseSeq : base string sequence for initial state
		:param fromStringFn : function or class passed string result of operations"""
		# base type to return sequence as

		self.prevSeq = str(baseSeq)
		self.fromStringFn = fromStringFn or str
		# sequence of diffs
		self.undoDiffs = []
		# [ [(diffDataA), (diffDataB)], [(diffDataC)] ] etc
		self.redoDiffs = []
		self.differ = difflib.Differ()

	def makeDiffData(self, seqA, seqB):
		data = []
		result = difflib.SequenceMatcher(
			isjunk=None,
			a=seqA,
			b=seqB,
			autojunk=False).get_opcodes()
		for op, aStartIndex, aEndIndex, \
			bStartIndex, bEndIndex in result:
			if op == "replace" : # can do dicts for portability
				data.append(self.replaceData(
					start=aStartIndex,
					end=aEndIndex,
				    data=seqB[ bStartIndex : bEndIndex ]))
			elif op == "insert" :
				data.append(self.insertData(
					index=aStartIndex,
					data=seqB[bStartIndex: bEndIndex]))
			elif op == "delete" :
				data.append(self.deleteData(
					start=aStartIndex, end=aEndIndex,
					data=seqA[aStartIndex:aEndIndex]))
		return data

	def applyDiffData(self, data, baseSeq=""):
		"""	given a single diff data tuple, apply it to the sequence
		and return it
		:param data: diff data namedtuple
		:param baseSeq:
		:return:
		"""
		if type(data) == self.replaceData:
			baseSeq = baseSeq[:data.start] + data.data + \
			          baseSeq[data.end:]
		elif type(data) == self.insertData:
			baseSeq = baseSeq[:data.index] + data.data + baseSeq[data.index:]
		elif type(data) == self.deleteData:
			baseSeq = baseSeq[:data.start] + baseSeq[data.end:]
		return baseSeq
		# return self.baseType(baseSeq)

	def do(self, newSeq):
		""" given new string sequence, extract diffs
		against existing previous sequence,
		append diff to stack """
		if newSeq == self.prevSeq:
			return
		result = self.makeDiffData(newSeq, self.prevSeq)
		self.undoDiffs.append(result)

		self.redoDiffs.clear()
		self.prevSeq = newSeq

	def undo(self):
		""" restore prevSeq to its previous state by applying last diff,
		then return it """
		undoData = self.undoDiffs.pop(-1)
		found = str(self.prevSeq)
		#for data in undoData[::-1]:
		for data in reversed(undoData):
			found = self.applyDiffData(data, found)

		# extract inverse deltas
		self.redoDiffs.append(self.makeDiffData(found, self.prevSeq))
		self.prevSeq = found
		return self.fromStringFn(found)

	def redo(self):
		""" apply inverse of undo change """
		redoData = self.redoDiffs.pop(-1)
		found = str(self.prevSeq)
		for data in reversed(redoData):
			found = self.applyDiffData(data, found)
		# extract inverse deltas
		self.undoDiffs.append(self.makeDiffData( found, self.prevSeq))
		self.prevSeq = found
		return self.fromStringFn(found)

	def serialise(self):
		""" return dict of all stored undo and redo actions """
		return {
			"seq" : self.prevSeq,
			"undo" : self.undoDiffs,
			"redo" : self.redoDiffs
		}

	@classmethod
	def fromDict(cls, data, sequence=None):
		obj = cls(sequence or data["sequence"])
		obj.undoDiffs = data["undo"]
		obj.redoDiffs = data["redo"]
		return obj


serialisedBase = "{'?VALUE': 'tree root', '?CHILDREN': [{'?VALUE': 'first branch', '?CHILDREN': [{'?VALUE': 'first leaf', '?NAME': 'leafA'}], '?NAME': 'branchA'}, {'?VALUE': 2, '?NAME': 'branchB'}], '?NAME': 'testRoot'}"

intermediate = "[{'?VALUE': 'first leaf', ___ '?NAME': 'leafA'}]"

serialisedNew = "{'?': 'tree ACSDADroot', '?CHILDREN': [{'?VALUE': 'first branch', '?CHILDREN': [{'?VALUE': 'NEW LEAF', '?NAME': 'leafA'}], '?NAME': 'branchA'}, {'?VALUE': 2, '?NAME': 'branchB'}], '?NAME': 'testRoot'}"

serialisedBase = "'?VALUE': 'tree root', '?CHILDREN'"
intermediate = "'?VALUE': tr_____ot', '?CHILDREN'"
serialisedNew = "'?VAL': 'tree', '?CHILDREN'"

if __name__ == '__main__':

	print("base", serialisedBase)

	obj = DiffUndo(serialisedBase)

	obj.do(intermediate)

	obj.do(serialisedNew)
	print("undo", obj.undo())
	print("undo", obj.undo())
	print("redo", obj.redo())
	print("redo", obj.redo())
	# print("undo", obj.undo())
	# print("redo", obj.redo())







def trimArgsKwargs(fn, givenArgs, givenKwargs=None):
	""" given function, and tuple and dict of args and kwargs,
	trim args to accepted length, and remove all but given kwargs from dict
	for use in signals - some functions just need to trigger
	on specific signals, while others may need more detail information passed
	to them
	"""
	argSpec = inspect.getfullargspec(fn)
	if argSpec.varargs:
		args = list(givenArgs)
	else:
		givenArgs = list(givenArgs)
		args = givenArgs[:min(len(argSpec.args), len(givenArgs))]

	if argSpec.varkw:
		kwargs = givenKwargs
	else:
		kwargs = {k : v for k, v in givenKwargs.items() if
		          k in argSpec.kwonlyargs}
	return (args, kwargs)

uniqueSign = "|@|" # something that will never appear in file path


def incrementName(name, currentNames=None):
	"""checks if name is already in children, returns valid one"""
	if currentNames and name not in currentNames:
		return name
	if name[-1].isdigit(): # increment digit like basic bitch
		new = int(name[-1]) + 1
		return name[:-1] + str(new)
	if name[-1] in string.ascii_uppercase: # ends with capital letter
		if name[-1] == "Z": # start over
			name += "A"
		else: # increment with letter, not number
			index = string.ascii_uppercase.find(name[-1])
			name = name[:-1] + string.ascii_uppercase[index+1]
	else: # ends with lowerCase letter
		name += "B"

	# check if name already taken
	if currentNames and name in currentNames:
		return incrementName(name, currentNames)
	return name


def safeLoadModule(modName, force=False, logFunction=None):
	"""takes string name of module
	"""
	logFunction = logFunction or print
	module = None
	if modName in sys.modules and not force:
		logFunction("module {} already loaded, skipping".format(modName))
		return sys.modules[modName]
	try:
		module = importlib.import_module(modName)
	except ImportError() as e:
		logFunction("ERROR in loading module {}".format(modName))
		logFunction("error is {}".format(str(e)))
	return module


def saveObjectClass(obj, regenFunc="fromDict", relative=True, uniqueKey=True,
					legacy=False):
	""" saves a module and class reference for any object
	if relative, will return path from root folder"""
	keys = [ "NAME", "CLASS", "MODULE", "regenFn" ]
	if uniqueKey: # not always necessary
		for i in range(len(keys)): keys[i] = "?" + keys[i]

	#path = convertRootPath(obj.__class__.__module__, toRelative=relative)
	path = obj.__class__.__module__
	if legacy: # old inefficient dict method
		return {
			keys[0]: obj.__name__,
			keys[1]: obj.__class__.__name__,
			keys[2]: path,
			keys[3]: regenFunc
		}
	data = uniqueSign.join([obj.__class__.__name__, path])
	return data


def loadObjectClass(objData):
	""" recreates a class object from any known module 
	:param objData : dict of form {
		"?MODULE" : module path,
		"?CLASS" : class name, }
		OR
		tuple of (class name, module path) """
	try:
		basestring
	except:
		basestring = str

	if isinstance(objData, dict):
		for i in ("?MODULE", "?CLASS"):
			if not objData.get(i):
				print("objectData {} has no key {}, cannot reload class".format(objData, i))
				return None
		path = objData["?MODULE"]
		className = objData["?CLASS"]


	elif isinstance(objData, (tuple, list)):
		# sequence [ class, modulepath, regenFn ]
		path = objData[1]
		className = objData[0]
	elif isinstance(objData, basestring):
		className, path = objData.split(uniqueSign)

	#module = convertRootPath( path, toAbsolute=True)
	module = path
	loadedModule = safeLoadModule(module)
	try:
		newClass = getattr(loadedModule, className)
		return newClass
	except Exception as e:
		print("ERROR in reloading class {} from module {}")
		print("has it moved, or module files been shifted?")
		print( "error is {}".format(str(e)) )
		return None