
import copy

import importlib

from types import FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType, LambdaType

from six import iteritems
import functools

import proxy
from proxy import Proxy
from lib import trimArgsKwargs


from main import Tree

""" so it turns out this is really hard 
like I've been dreaming about it for months hard """

""" 'live inheritance' is achieved by passing out a proxy object wrapper,
and repeatedly regenerating proxy object data, 
while comparing to given base object

2 problems must be solved:
 - how do we deal with complex and deep objects
 - how do we make a mask of a mask
 
proxy actually has two components:
 - list of (mutable) transformations to perform on data from base object
 - end interface for accessing that data

the delta-tracking behaviour would be a type of transformation -
or should output a type of transformation, which can be applied or reversed,
not necessarily by the specific delta process

a similar transformation could run over data to mirror it in space, for example

reversibility is not important for this use, but it may make the result
more robust as a whole to pursue it

Q: why don't I use deepdiff?
A: I need 2.7 support for now, also deepdiff is too
complicated for me to understand easily if something goes wrong with it
"""



class Transform(object):
	""" represents a (reversible?) transformation
	to be applied to a given object """


# def f():
# 	pass

class CallWrapper(object):
	""" pseudo-decorator
	for pre- and post-call wrapping of specific function
	either subclass for special behaviour
	or just pass in specific functions to run

	replaceResult allows post call to intercept
	base function result
	"""
	def __init__(self, fn, beforeFn=None, afterFn=None,
	             passParams=False,
	             replaceResult=False,
	             *args, **kwargs):
		self.fn = fn
		self.beforeFn = beforeFn
		self.afterFn = afterFn
		self.replaceResult = replaceResult
		self.passParams = passParams

	def preCall(self, *args, **kwargs):
		#print("preCall")
		if self.beforeFn:
			#print("beforeFn", self.beforeFn)
			args, kwargs = trimArgsKwargs(self.beforeFn, args, kwargs)
			#print("trimArgs")
			result = self.beforeFn(*args, **kwargs)
		return args, kwargs

	def postCall(self, result, *args, **kwargs):
		if self.afterFn:
			#print("post call")
			args = [result] + list(args)
			args, kwargs = trimArgsKwargs(self.afterFn, args, kwargs)
			fnResult = self.afterFn(*args, **kwargs)

		return result

	def __call__(self, *args, **kwargs):
		# args, kwargs = self.preCall(*args, **kwargs)
		self.preCall(*args, **kwargs)
		print("")
		print("main call", self.fn, args, kwargs)
		result = self.fn(*args, **kwargs)
		# result = self.postCall(result, *args, **kwargs)
		self.postCall(result, *args, **kwargs)
		return result

class Delta(Proxy):
	""" delta-tracking wrapper

	it is necessary to shuffle the stages regarding when
	the "live" proxy is returned, and when we want the output
	of the delta

	_stack is the list of accrued transforms
	_mask is the final mask to apply to object?


	__baseObjRef is the live object
	__proxyObjIntermediate is an internal variable safe from
		main proxy machinery



	_proxyObj property now returns a new object each time -
	the _product of the live base object with the delta's mask


	"""
	_proxyAttrs = ("_mask",
	               "_stack",
	               "_baseObj",
	               "_baseObjRef",
	               "_proxyObjIntermediate",
	               )
	_deltaMethods = (
		"_product", "_extractMask", "_applyMask"
	)

	def __init__(self, obj, deep=False):
		super(Delta, self).__init__(obj)
		#print("proxyAttrs", self._proxyAttrs)
		self._baseObj = obj # reference to base object to draw from
		c = self._copyBaseObj()
		self._proxyObj = c
		self._mask = { "added" : {}, "modified" : {}, "removed" : {} }
		#self._extractMask(baseObj=self._baseObj, deltaObj=self._proxyObj)

	def __getattr__(self, item):

		if item in self.__dict__.keys():
			return object.__getattribute__(self, item)

		#self._applyMask(self._copyBaseObj(), setProxy=True)
		result = super(Delta, self).__getattr__(item)
		if isinstance(result, (
				MethodType, FunctionType,
				BuiltinFunctionType, BuiltinMethodType,
				LambdaType
		)):
			#print("wrapping ", item)
			# print("fn bound base {}".format(result.__self__ is
			#                                 self._baseObj))
			# print("fn bound proxy {}".format(result.__self__ is
			#                                 self._proxyObj))
			applyLam = lambda : self._applyMask(
				self._copyBaseObj(),
				#self._baseObj,
				setProxy=True)
			extractLam = lambda : self._extractMask()
			# wrap = CallWrapper(result, beforeFn=self._applyMask,
			#                    afterFn=self._extractMask)
			wrap = CallWrapper(result,
			                   #beforeFn=applyLam,
			                   afterFn=extractLam
			                   )
			result = wrap
		return result

	@property
	def _proxyObj(self):
		""" _proxyObj on delta proxy always returns PRODUCT
		internally, access the true current proxy object with
		_proxyObjRef """
		return self._product()

	@_proxyObj.setter
	def _proxyObj(self, val):
		self._proxyObjRef = val


	def _copyBaseObj(self):
		""" returns new copy of base object - override for
		more complex objects"""
		#obj = obj or self._baseObj
		obj = self._baseObj
		return copy.copy(obj)

	@property
	def _baseObj(self):
		""" return the live base object known to the delta -
		this is the same as Proxy's _proxyObj """
		return self._baseObjRef
	@_baseObj.setter
	def _baseObj(self, obj):
		self._baseObjRef = obj

	# def _returnProxy(self):
	# 	""" runs mask operation every time proxy is accessed
	# 	never said this would be fast """
	# 	return self._product()


	def _extractMask(self, baseObj=None, deltaObj=None):
		""" compares proxy object to base, collates delta to mask """
	def _applyMask(self, newObj=None, setProxy=False):
		""" applies delta mask to _product object
		_product object is passed in as basic copy
		of base object """

	def _product(self):
		# self._extractMask(self._baseObj, self._proxyObjRef)
		#debug(self._mask)
		newObj = copy.copy(self._baseObj)
		self._applyMask(newObj)
		self._proxyObjRef = newObj
		return newObj

	def serialise(self):
		pass

	@classmethod
	def deserialise(cls, data, baseObj):
		""" loads delta object from dict and reapplies to baseObj """
		pass


def deltaTypeForObj(obj):
	""" very primitive for now """
	if isinstance(obj, dict):
		return DictDelta
	elif hasattr(obj, "__len__"):
		return ListDelta
	else:
		return None

class ListDelta(Delta):
	""" basic, indices not working """

	def __init__(self, obj, deep=False):
		super(ListDelta, self).__init__(obj, deep)
		if deep:
			# iterate over list entries to check for complex data
			for i, entry in enumerate(self):
				# if entry is complex, wrap it with a delta object
				if deltaTypeForObj(entry):
					continue
					self[i] = deltaTypeForObj(entry)(entry, deep=True)
					self._proxyChildren.add(self[i])

	def _extractMask(self, baseObj=None, deltaObj=None):
		#print("extractMask", self._mask)
		#print(self._baseObj, self._proxyObjRef)
		#print(self._mask)
		self._mask["added"] = {
			self._proxyObjRef.index(i) : i for i in self._proxyObjRef \
				if not i in self._baseObj }

		#print("mask", self._mask)

	def _applyMask(self, newObj=None, setProxy=False):
		#print("applyMask", newObj)
		#print("mask {}".format(self._mask))
		# print("newObj {} base".format(newObj is self._baseObj))
		# print("newObj {} proxy".format(newObj is self._proxyObj))
		# return

		for index, val in iteritems(self._mask["added"]):
			try:
				newObj.insert(index, val)
			except:
				newObj.append(val)
		# # maybe
		if setProxy:
			#self._proxyObj = newObj
			self._proxyObjRef = newObj
		return newObj

"""
before looking up ANYTHING or any method on delta, extract new
object from applying the mask and update the proxy obj
"""

class DictDelta(Delta):

	def __init__(self, obj, deep=False):
		super(DictDelta, self).__init__(obj, deep)
		if deep:
			# iterate over list entries to check for complex data
			for i, entry in enumerate(self):
				# if entry is complex, wrap it with a delta object
				if deltaTypeForObj(entry):
					self[i] = deltaTypeForObj(entry)(entry, deep=True)
					self._proxyChildren.add(self[i])

	def _extractMask(self, proxyObj=None):
		self._mask["added"] = {
			pK : pV for pK, pV in self._proxyObj.iteritems() if \
				pK not in self._baseObj }
		self._mask["modified"] = {
			pK : pV for pK, pV in self._proxyObj.iteritems() if \
				self._baseObj.get(pK) != pV }
		# added and modified functionally the same here

	def _applyMask(self, newObj=None):
		self._proxyObj.update(self._mask["added"])
		self._proxyObj.update(self._mask["modified"])



class TreeDelta(Delta):
	""" final boss """

	def __init__(self, obj):
		""" a mask initialised on a tree then create
		masks all the way down? probably
		"""
		super(TreeDelta, self).__init__(obj)
		for branch in obj.branches:
			""" vulnerable to name changing, need proper hashing for
			branch objects """
			self._mask["modified"][branch.name] = branch


	def _extractMask(self, baseObj=None, deltaObj=None):
		""" avoid looking up instance attributes here
		this should probably be static """
		# added trees are easiest, no child deltas needed
		# for branch in baseObj.branches:
		# 	if
		self._mask["added"] = {
			branch.index() : branch for branch in deltaObj.branches \
				if not branch.name in baseObj._map
		} # need better index integration
		# store indices separately? idk
		self._mask["modified"] = { # modified is list of child masks
		}
		""" modifications have no hierarchy in deltamask,
		mask should only track value and added and removed branches
		otherwise lookup tree objects and create new delta objects?
		but then how the hell do you serialise and deserialise """


		if deltaObj.value != baseObj.value:
			self._mask["value"] = deltaObj.value
		else: self._mask["value"] = None


	def _applyMask(self, newObj=None):
		for index, branch in self._mask["added"].iteritems():
			newObj.addChild(branch, index)
		if self._mask.get("value") is not None:
			newObj.value = self._mask["value"]

	def serialise(self):
		data = {
			"added" : {},
			"value" : self._mask["value"]
		}
		for index, branch in self._mask["added"]:
			data["added"][index] = branch.serialise()

	@classmethod
	def deserialise(cls, data, baseObj):
		""" setting redundant values on proxy is fine as
		_extractMask() will remove them anyway """
		proxy = cls(baseObj)
		for index, branchData in data["added"]:
			branch = Tree.fromDict(branchData)
			proxy.addChild(branch, index=index)

		proxy.value = data["value"]






"""
# toughest scenario:
baseObj
proxy = Delta(baseObj)
proxy["key"] = valueA
baseObj["key"] = valueB

proxy["key"] = ...?
easiest way is to say any "set" command overrides the base

"""
# test for interfaces with the tree structure
testTree = Tree("TestRoot")
testTree("asdf").value = "firstKey"
testTree("parent").value = "nonas"
testTree("parent.childA").value = 930
testTree("parent.childA").extras["options"] = (930, "eyyy")
#testTree("parent.childB").value = True

# cannot do nested list inputs yet
#testTree["parent.listEntry"] = "[eyyy, test, 4.3, '', 2e-10, False]"
#testTree["parent.nestedList"] = "[eyyy, test, 4.3, '', [4e4, i, 33, True], 2e-10]"




if __name__ == '__main__':
	pass

	# baseDict = {"a" : "b", 45 : 64}
	# proxyDict = DictDelta(baseDict)
	#
	#
	#

	# proxyTree = TreeDelta(testTree)
	#
	# proxyTree["proxyKey"] = "w e w _ l a d"
	# proxyTree["parent"] = 12323422
	# proxyTree.value = 4956565
	#
	# print(proxyTree.display())
	#
	# proxyTree["proxyKey.proxyChild"] = "jojojo"
	#
	# print(proxyTree.display())
	# print(testTree.display())



	# baseDict = {"baseKey" : 69,
	#             "baseKeyB" : "eyy"}
	# debug(baseDict)
	#
	# replaceDict = {"replacedDict" : 3e4}

	# testDict = Proxy(baseDict)
	# testDict["proxyTest"] = True
	# debug(testDict)
	# testDict._proxyObj = replaceDict
	# debug(testDict)
	#
	# proxyDict = Delta(baseDict)
	# debug(proxyDict)
	#
	# baseDict["newBaseKey"] = 49494
	# debug(proxyDict)
	#
	# proxyDict["newProxyKey"] = "FAJLS"
	# print("baseDict is {}".format(baseDict))
	# debug(proxyDict)



