
import copy

from types import FunctionType, MethodType, BuiltinFunctionType, BuiltinMethodType, LambdaType

from dev.proxy import Proxy
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

a transformation might be defined on a simple tuple, or on
an entire tree -
absolutely no idea how to represent it properly in ui.
Might be overkill to even formalise this in objects at all,
just use the normal delta system, along with specific
tool actions


in the new structure, we have both a custom transform proxy container
and a separate delta object,
for each new class 

"""

class Transform(object):
	""" atomic transformation on data """
	# def apply(self):
	# 	raise NotImplementedError
	# 	pass
	# def revert(self):
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


class TransformProxy(Proxy):
	""" delta-tracking wrapper

	proxy maintaining a stack of transformations to perform
	on this object - on query, stack is applied
	and nw result object returned

	"""
	_proxyAttrs = ("_transformStack",
	               "_baseObj",
	               "_baseObjRef",
	               "_proxyObjIntermediate",
	               )

	def __init__(self, obj, deep=False):
		super(TransformProxy, self).__init__(obj)
		self._baseObj = obj # reference to base object to draw from
		c = self._copyBaseObj()
		self._proxyObj = c
		self._transformStack = []

	def __getattr__(self, item):

		if item in self.__dict__.keys():
			return object.__getattribute__(self, item)

		#self._product(updateSelf=True)
		self._proxyObjRef = self._product()
		result = super(TransformProxy, self).__getattr__(item)
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

	def _applyStack(self, newObj=None):
		""" applies delta mask to newObj
		_product object is passed in as basic copy
		of base object """
		return newObj


	def _product(self):
		""" returns product of base object
		with transformation stack """
		newObj = self._copyBaseObj()
		newObj = self._applyStack(newObj)
		return newObj

	def serialise(self):
		pass

	@classmethod
	def deserialise(cls, data, baseObj):
		""" loads delta object from dict and reapplies to baseObj """
		pass

class DeltaProxy(TransformProxy):
	""" delta-tracking wrapper

	the FINAL result of main transform stack
	is taken as the base object - between it and the proxy
	object, delta ops are added to the delta stack,
	which runs on top of the transform stack
	use difflib for this afterall

	"""
	_proxyAttrs = ("_deltaStack",
	               )

	def __init__(self, obj, deep=False):
		super(DeltaProxy, self).__init__(obj)
		self._deltaStack = []

	def __getattr__(self, item):

		if item in self.__dict__.keys():
			return object.__getattribute__(self, item)

		result = super(DeltaProxy, self).__getattr__(item)
		if isinstance(result, (
				MethodType, FunctionType,
				BuiltinFunctionType, BuiltinMethodType,
				LambdaType
		)):
			# extractLam = lambda: self._extractDeltas(
			# 	self._transformProduct(), self._proxyObjRef)
			def _postCallExtract():
				self._extractDeltas(
					self._transformProduct(), self._proxyObjRef)
				print("post proxy", self._proxyObjRef)



			wrap = CallWrapper(result,
			                   #beforeFn=applyLam,
			                   # afterFn=extractLam
			                   afterFn=_postCallExtract
			                   )
			result = wrap
		return result


	def _extractDeltas(self, baseObj=None, deltaObj=None):
		""" compares proxy object to base, collates delta to mask
		BEWARE this will only compare against the
		BASE TRANSFORM PRODUCT.
		"""
		raise NotImplementedError

	def _applyDeltas(self, newObj=None, setProxy=False):
		""" applies delta mask to _product object
		_product object is passed in as basic copy
		of base object """
		raise NotImplementedError

	def _transformProduct(self):
		return super(DeltaProxy, self)._product()

	def _product(self):
		""" g"""
		transformProduct = self._transformProduct()
		transformProduct = self._applyDeltas(transformProduct)
		return transformProduct



def deltaTypeForObj(obj):
	""" very primitive for now """
	if isinstance(obj, dict):
		return DictDelta
	elif hasattr(obj, "__len__"):
		return ListDeltaProxy
	else:
		return None




class ListDeltaProxy(DeltaProxy):
	""" basic, indices not working """

	def __init__(self, obj, deep=False):
		super(ListDeltaProxy, self).__init__(obj, deep)
		if deep:
			# iterate over list entries to check for complex data
			for i, entry in enumerate(self):
				# if entry is complex, wrap it with a delta object
				if deltaTypeForObj(entry):
					continue
					self[i] = deltaTypeForObj(entry)(entry, deep=True)
					self._proxyChildren.add(self[i])

	def _extractDeltas(self, baseObj=None, deltaObj=None):
		print("list extract")
		print(baseObj, deltaObj)
		self._deltaStack = ListDelta.extractDeltas(baseObj, deltaObj)
		print("stack", self._deltaStack)
		pass

	def _applyDeltas(self, newObj=None, setProxy=False):

		print(self._deltaStack)
		self._deltaStack.reverse()
		print((self._deltaStack))
		for opData in (self._deltaStack):
			newObj = ListDelta.applyDelta(opData, newObj)
		print("newObj ", newObj)
		return newObj

"""
before looking up ANYTHING or any method on delta, extract new
object from applying the mask and update the proxy obj
"""

class DictDelta(DeltaProxy):

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



class TreeDelta(DeltaProxy):
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

#
# from pprint import pprint
# base = ["a", "b", ["abffd", 59, 4], "h", {49 : "v"}, 5]
# d = ["a", ["abffd", 59, 5], "h", {"help" : "me"}, {49 : "v"}, "s", 5, "jjf"]
#
# for l in [base, d]:
# 	for i, val in enumerate(l):
# 		try:
# 			hash(val)
# 		except:
# 			l[i] = tuple(val)
#
#
# # base = ["a", "b"]
# # d = ["a", "b", "c"]
#
# matcher = difflib.SequenceMatcher(
# 	isjunk=None, a=base, b=d, autojunk=False
# )
#
# ops = matcher.get_opcodes()
# pprint(ops)
#
# groups = matcher.get_grouped_opcodes()
#


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

