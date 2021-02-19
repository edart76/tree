
import copy

from proxy import Proxy
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

class Delta(Proxy):
	""" delta-tracking wrapper
	also adapted from 496741 """
	_proxyAttrs = ("_baseObj", "_mask")

	def __init__(self, obj, deep=False):
		super(Delta, self).__init__(obj)
		self._baseObj = obj # reference to base object to draw from
		self._proxyObjRef = copy.copy(obj)
		self._mask = { "added" : {}, "modified" : {}, "removed" : {} }
		self._extractMask(self._baseObj, self._proxyObjRef)

	def _returnProxy(self):
		""" runs mask operation every time proxy is accessed
		never said this would be fast """
		#return super(Delta, self)._returnProxy()
		return self.product()


	def _extractMask(self, baseObj=None, deltaObj=None):
		""" compares proxy object to base, collates delta to mask """
	def applyMask(self, newObj=None):
		""" applies delta mask to product object """

	def product(self):
		self._extractMask(self._baseObj, self._proxyObjRef)
		#debug(self._mask)
		newObj = copy.copy(self._baseObj)
		self.applyMask(newObj)
		self._proxyObjRef = newObj
		return newObj

	def serialise(self):
		pass

	@classmethod
	def deserialise(cls, data, baseObj):
		""" loads delta object from dict and reapplies to baseObj """
		pass

# class ProxyDelta(Proxy, Delta):
#
# 	_proxyAttrs = (#"_proxyObjRef", "_proxyObj",
# 	               "_baseObj", "_mask")


def deltaTypeForObj(obj):
	""" very primitive for now """
	if isinstance(obj, dict):
		return DictDelta
	elif hasattr(obj, "__len__"):
		return ListDelta
	else:
		return None


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

	def applyMask(self, newObj=None):
		self._proxyObj.update(self._mask["added"])
		self._proxyObj.update(self._mask["modified"])

class ListDelta(Delta):
	""" basic, indices not working """

	def __init__(self, obj, deep=False):
		super(ListDelta, self).__init__(obj, deep)
		if deep:
			# iterate over list entries to check for complex data
			for i, entry in enumerate(self):
				# if entry is complex, wrap it with a delta object
				if deltaTypeForObj(entry):
					self[i] = deltaTypeForObj(entry)(entry, deep=True)
					self._proxyChildren.add(self[i])

	def _extractMask(self):
		self._mask["added"] = {
			self._proxyObj.index(i) : i for i in self._proxyObj \
				if not i in self._baseObj }
	def applyMask(self, newObj=None):
		for index, val in self._mask["added"]:
			try:
				self._proxyObj.insert(index, val)
			except:
				self._proxyObj.append(val)


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


	def applyMask(self, newObj=None):
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



