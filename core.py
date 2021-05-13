
""" mutable tree data structure
 base functionality before any other modules """
from __future__ import annotations
from sys import version_info

from tree.lib import incrementName, saveObjectClass, loadObjectClass, \
	uniqueSign

import pprint, uuid
from collections import OrderedDict
from enum import Enum
from tree.signal import Signal
from typing import List, Union
from six import iteritems, string_types

"""TODO :
- Proper solution for looking up matching values on parent branches,
	via getInherited(). Maybe a key lambda / function, like sorted()?
	Also ensure we respect breakpoints in tree - if a tree is a breakpoint,
	it acts like a root for all trees under it
- Proper iterators, as with os.walk()
- Figure out how to treat the modification signals -
	stack frames vs consolidation
		- Testing a compromise - individual branches only trigger their 
		own signal, and those of root. Connect to branch if you want specific,
		or root if you want view of entire tree
"""

####### THE MAIN EVENT ########
# sep = "."
# separator = "/"
# parentToken = "^" # directs to the tree's parent
# parentToken = .."

class TreeBase(object):
	"""fractal tree-like data structure
	each branch having both name and value

	extras is unordered dict of any random auxiliary information.

	tree addressing was originally inspired by maya attribute syntax,
	expecting string of "a.b.c" etc

	"""

	# child and parent tokens for addresses
	sep = "."
	parentToken = "^"
	# these can be reset directly on tree instances to customise syntax

	branchesInherit = False

	debugOn = False

	class StructureEvents(Enum):
		branchAdded = 1
		branchRemoved = 2
		#branchRenamed = 3

	# keys in extras that play important roles
	extraKeys = ("default", "readOnly", "active", "breakpoint")

	# kwargs that may be passed with lookup
	lookupKwargs = {
		"create" : True, # should branch be created if not found
		"extras" : None, # 'extra' values to be set on branch creation
		"case": True,  # should lookup respect casing
	}

	def __init__(self, name=None, val=None,
	             branches=None, # will be added in future
	             ):
		self._name = str(name) if name else None
		self._uuid = None
		self._parent = None
		self._value = val

		self._branchMap = OrderedDict()
		self.extras = {}
		self.overrides = {}

		# signals - on branch changing, all parent branch signals
		# will be activated
		self._signalsActive = True
		# valueChanged signature: branch, oldValue, newValue
		self.valueChanged = Signal()
		# nameChanged signature: branch, oldName, newName
		self.nameChanged = Signal()
		# structureChanged signature: branch, parent, event code
		self.structureChanged = Signal()

		self.signals = (self.valueChanged,
		                self.nameChanged,
		                self.structureChanged)

		# read-only attr
		self.readOnly = False
		self.active = True

	@classmethod
	def _defaultCls(cls):
		"""Tree class to use for leaves by default"""
		return TreeBase

	@property
	def name(self)->str:
		return self._name

	@name.setter
	def name(self, val):
		""" update parent map """
		self._setName(str(val))

	@property
	def uuid(self):
		""" no idea if this is used correctly here """
		if not self._uuid:
			self._uuid = uuid.uuid4()
		return self._uuid

	@property
	def parent(self)->TreeBase:
		""":rtype AbstractTree"""
		return self._parent
	@parent.setter
	def parent(self, val:TreeBase):
		""" this should be removed, addChild is the correct way to do it """
		self._setParent(val)

	@property
	def siblings(self)->List[TreeBase]:
		if self.parent:
			return self.parent.branches.remove(self)
		return []

	@property
	def root(self)->TreeBase:
		"""returns root tree object
		consider possibly denoting arbitrary points in tree as breakpoints,
		roots only to branches under them """
		return self.parent.root if self.parent else self

	@property
	def leaves(self)->List[TreeBase]:
		"""returns branches under this branch
		which do not have branches of their own"""
		return [i for i in self.allBranches(False) if not i.branches]

	@property
	def address(self)->str:
		return self._address()

	@property
	def default(self):
		return self.extras.get("default")
	@default.setter
	def default(self, val):
		self.extras["default"] = val

	@property
	def value(self):
		if self._value is None and "default" in self.extras:
			self._value = self.extras["default"]
		return self._value
	@value.setter
	def value(self, val):
		oldVal = self._value
		self._value = val
		if oldVal != val:
			self.valueChanged(self, oldValue=oldVal, newValue=val)

	@property
	def branches(self)->List[TreeBase]:
		"""more explicit that it returns the child tree objects
		:rtype list( AbstractTree )"""
		return list(self._branchMap.values())

	def debug(self, info):
		if self.debugOn:
			print(info)

	def _branchFromToken(self, token):
		""" given single address token, return a known branch or none """

	@classmethod
	def _parseAddressTokens(cls, tokenArgs):
		""" returns uniform list from address tokens
		direct lookup in this way will probably always be simple
		more complex logic should be handled by other functions,
		for ease of reading
		:type tokenArgs : tuple"""
		result = []
		for token in tokenArgs:
			if isinstance(token, string_types):
				result += list(token.split(cls.sep))
			elif isinstance(token, (list, tuple)):
				result += cls._parseAddressTokens(token)
		return result



	def __call__(self, *address, **kwargs)->TreeBase:
		""" allows lookups of string form "root.branchA.leaf"
		kwargs will be passed to extras

		__call__ will never allow lookup by indexing -
		tree(2) searches for the branch named "2"
		to do this, use:
		tree.branches[2]

		more explicit, more normal than using __call__ with index

		:returns AbstractTree
		:rtype AbstractTree"""
		self.debug(("args", address))
		if not address:
			return self
		address = self._parseAddressTokens(address)

		# all input coerced to list
		first = str(address.pop(0))
		if first == self.parentToken: # aka unix ../
			return self.parent(address)
		if not first in self._branchMap: # add it if doesn't exist
			if self.readOnly:
				raise RuntimeError( "readOnly tree {} accessed improperly - \n"
									"no address {}".format(self, first))
			# check if branch should inherit directly, or
			# remain basic tree object
			if self.branchesInherit:
				obj = self.__class__(first, None)
			else:
				obj = self._defaultCls()(first, None)
			# set extras from given keys -
			for key in self.extraKeys:
				if key in kwargs.get("extras", []):
					obj.extras[key] = kwargs[key]
			self.debug(("added obj", obj))
			branch = self.addChild(obj)

		else: # branch name might be altered
			branch = self._branchMap[first]
			self.debug(("found branch", branch))

		return branch(*address, **kwargs)

	def __getitem__(self, address, **kwargs):
		""" returns direct value of lookup branch
		"""
		return self(address, **kwargs).value

	def __setitem__(self, key, value, **kwargs):
		""" assuming that setting tree values is far more frequent than
		setting actual tree objects """
		self(key, **kwargs).value = value

	def __repr__(self):
		return "<{} ({}) : {}>".format(self.__class__, self.name, self.value)

	def __copy__(self)->TreeBase:
		""" create shallow copy of this tree -
		new tree object, new internal map, same
		tree objects in map """
		tree = self.__class__(self.name)
		if self.value is not None:
			tree.value = type(self.value)(self.value)
		tree._branchMap = OrderedDict(self._branchMap)
		return tree

	def __deepcopy__(self)->TreeBase:
		""":returns Tree"""
		return self.fromDict(self.serialise())

	def __iter__(self):
		"""iterate over branches"""
		return self._branchMap.values().__iter__()

	def __contains__(self, item):
		""" I found strict 'is' check more often useful
		use containsEq for equivalence """
		if isinstance(item, TreeBase):
			return self.contains(item, equivalent=False)
		return False

	def __eq__(self, other):
		""" equivalence considers value, branch names and extras
		for exact comparison use 'is' """
		if isinstance(other, TreeBase):
			return self.isEquivalent(other)
		return NotImplementedError

	def __lt__(self, other):
		if not isinstance(other, TreeBase):
			raise TypeError(
				"comparison not supported with {}".format(
					other, other.__class__))
		return self.name < other.name

	def __hash__(self):
		""" hash is unique per object """
		return hash(self.uuid)
	
	def __del__(self):
		super(TreeBase, self).__del__()


	def activateSignals(self):
		self._signalsActive = True
		for i in self.signals:
			i.activate()
	def muteSignals(self):
		self._signalsActive = False
		for i in self.signals:
			i.mute()

	def _setParent(self, parent):
		"""sets new abstractTree to be parent"""
		self._parent = parent
		if parent: # setting to none can happen
			"""EITHER we literally supplant the signal of the child 
			branch with that of the parent,
			OR connect signals to parents (current method)
			
			this is the most flexible, but every signal is a new frame,
			so stack traces may get c r a z y
			"""
			for i in self.signals:
				i.clear()
			self.valueChanged.connect(parent.root.valueChanged)
			self.structureChanged.connect(parent.root.structureChanged)
			self.nameChanged.connect(parent.root.nameChanged)

	def addChild(self, branch, index=None, force=False):
		if branch in self: # same object
			print("cannot add existing branch, named " + branch.name)
			return branch
		if not force: # increment name until valid name found
			while branch.name in self.keys():
				branch._setName(incrementName(
					branch.name, self.keys()))

		if index is None:
			self._branchMap[branch.name] = branch
		else: # more complex ordered dict management
			newMap = OrderedDict()
			oldBranches = list(self._branchMap.values())
			if index > len(oldBranches) - 1:
				index = len(oldBranches)
			oldBranches.insert(index, branch)
			for newBranch in oldBranches:
				newMap[newBranch.name] = newBranch
			self._branchMap = newMap
		branch._setParent(self)

		# emit signal
		self.structureChanged(branch, self,
		                      self.StructureEvents.branchAdded)
		return branch


	def getBranch(self, lookup, default=None, **kwargs)->Union[TreeBase, None]:
		""" returns branch object if it exists or default
		only supports single level """
		lookup = self._parseAddressTokens((lookup,))
		if not lookup:
			return self
		name = lookup.pop(0)
		if name not in self._branchMap.keys():
			return default
		if lookup:
			return self._branchMap[name].getBranch(lookup)
		return self._branchMap[name]

	def get(self, lookup, default=None):
		""" same implementation as normal dict
		addresses will recurse into child branches
		duplication here from main address system, fix it
		RETURNS VALUE"""
		result = self.getBranch(lookup)
		if result:
			return result.value
		return default

	####### DISABLED for now ######
	# def getInherited(self, lookup, default=None):
	# 	""" searches this branch and all ancestors for occurrences
	# 	of lookup, then returns its value """
	# 	return self.get(lookup,
	# 	                self.parent.getInherited(lookup, default)
	# 		if self.parent else default)
	###### need to find a good way to handle this #####

	def index(self, lookup=None, *args, **kwargs):
		if lookup is None: # get tree's own index
			return self.ownIndex()
		if lookup in self._branchMap.keys():
			return list(self._branchMap.keys()).index(lookup, *args, **kwargs)
		else:
			return -1

	def ownIndex(self):
		if self.parent:
			return self.parent.index(self.name)
		else: return -1

	def flattenedIndex(self):
		""" return the index of this branch if entire tree were flattened """
		index = self.index()
		if self.parent:
			index += self.parent.flattenedIndex() + 1
		return index

	def keys(self):
		return self._branchMap.keys()

	def iterBranches(self):
		# return self._branchMap.items()
		return iteritems(self._branchMap)

	def allBranches(self, includeSelf=True, depthFirst=True)->List[TreeBase]:
		""" returns list of all tree objects
		depth first
		:returns [Tree]"""
		found = [ self ] if includeSelf else []
		if depthFirst:
			for i in self.branches:
				found.extend(i.allBranches(
					includeSelf=True, depthFirst=True))
		else:
			found.extend(self.branches)
			for i in self.branches:
				found.extend(i.allBranches(
					includeSelf=False, depthFirst=False))
		return found

	def iterAllBranches(self):
		""" not necessary yet, but will be for colossal trees
		like file systems
		"""
		pass

	def isEquivalent(self, branch, includeBranches=True):
		""" tests if this tree is equivalent to
		the given object """
		flags = [
			self.name == branch.name,
			self.value == branch.value,
			self.extras == branch.extras
		]
		if includeBranches:
			flags.append(all([i.isEquivalent(n)
				for i, n in zip(self.branches, branch.branches)]))
		return all(flags)

	def contains(self, branch, equivalent=True):
		""" more explicit contains check, allowing for equivalence,
		inheritance, etc
		"""
		if equivalent:
			return any([branch.isEquivalent(i) for i in self.branches])
		else:
			return any([branch is i for i in self.branches])


	def _address(self, prev=None):
		"""returns list path from root to this tree
		does not include root
		return list of string addresses
		"""
		prev = prev or []
		if self.root == self:
			return prev
		prev.insert(0, self.name)
		return self.parent._address(prev=prev)

	def stringAddress(self)->str:
		""" returns the address sequence joined by the tree separator """
		return self.sep.join(self.address)

	def search(self, path, onlyChildren=True):
		""" searches branches for trees matching a partial path,
		and returns ALL THAT MATCH
		so for a tree
		root
		+ branchA
		  + leaf
		+ branchB
		  + leaf
		search("leaf") -> two trees
		right now would also return both for search( "lea" ) -
		basic contains check is all I have

		if onlyChildren, only searches through children -
		else checks through all branches
		"""

		found = []
		if path in self.name:
			found.append(self)
		toCheck = self.branches if onlyChildren else self.allBranches(True)
		for i in toCheck:
			found.extend( i.search(path) )
		return found


	def _setName(self, name):
		"""renames and syncs parent's map
		currently destroys orderedDict order - oh well"""
		if name == self._name: # we aint even mad
			return name

		oldName = self._name

		# we need to preserve order across renaming
		if self.parent:
			newDict = OrderedDict()
			oldName = self._name
			name = incrementName(name, self.parent.keys())
			for k, v in self.parent.iterBranches():
				if k == oldName:
					newDict[name] = self
					continue
				newDict[k] = v
			self.parent._branchMap = newDict
		self._name = name
		self.nameChanged(self, oldName, name)
		return name

	def remove(self, address=None):
		"""removes address, or just removes the tree if no address is given"""
		if not address:
			if self.parent:
				self.parent._branchMap.pop(self.name)

				self.parent.structureChanged(self, self.parent,
				                             self.StructureEvents.branchRemoved)
				return self
		branch = self(address)
		branch.remove()
		branch.parent.structureChanged(branch, branch.parent,
		                               self.StructureEvents.branchRemoved)
		return branch


	def setIndex(self, index):
		""" reorders tree branch to given index
		negative indices not yet supported """
		if not self.parent:
			return
		if index < 0: # ?
			index = len(self.siblings) + index
		newMap = OrderedDict()
		oldKeys = list(self.parent._branchMap.keys())
		oldKeys.remove(self.name)
		oldKeys.insert(index, self.name)
		for key in oldKeys:
			newMap[key] = self.parent._branchMap[key]
		self.parent._branchMap = newMap


	def searchReplace(self, searchFor=None, replaceWith=None,
	                  names=True, values=True, recurse=True):
		"""checks over raw string names and values and replaces"""
		branches = self.allBranches(True) if recurse else [self]
		for branch in branches:
			if names:
				branch.name = str(branch.name).replace(searchFor, replaceWith)
			if values:
				branch.value = str(branch.value).replace(searchFor, replaceWith)


	def matches(self, other):
		""" check if name, value and extras match
		another given branch """
		return all([getattr(self, i) == getattr(other, i)
		            for i in ("_branchMap", "_value", "_name", "extras")])


	@classmethod
	def fromDict(cls, regenDict)->TreeBase:
		"""expects dict of format
		name : eyy
		value : whatever
		children : [{
			etc}, {etc}]
			:param regenDict : Dict """

		# support subclass serialisation and regen -
		# check first for a saved class or module name
		objData = regenDict.get("objData") or {}
		if objData:
			cls = loadObjectClass(objData) or cls._defaultCls()

		# if branch is same type as parent, no info needed
		# a tree of one type will mark all branches as same type
		# until a new type is flagged
		val = regenDict.get("?VALUE") or None
		name = regenDict.get("?NAME") or None
		children = regenDict.get("?CHILDREN") or []
		if not (val or name or children): # skip branch
			print("regenDict {}".format(regenDict))
			print("no name, val or children found")
			return None
		new = cls(name=name, val=val)
		new.extras = regenDict.get("?EXTRAS") or {}

		# regnerate children
		for i in children:
			branch = cls.fromDict(i)
			if branch is None:
				continue
			# replace existing (default) branches declared in init
			new.addChild(branch, force=True)
		return new


	def rootData(self):
		"""Returns any data needed to describe the whole tree
		in its serialised state -
		for now nothing"""
		return {
		}

	def serialise(self, includeAddress=False)->dict:
		serial = {
			"?NAME" : self.name,
		}
		if includeAddress:
			serial["?ADDR"] = self.address
		if self.value is not None:
			# can be dicey with complex types
			serial["?VALUE"] = self.value
		if self.branches:
			serial["?CHILDREN"] = [i.serialise() for i in self._branchMap.values()]
		if self.extras:
			serial["?EXTRAS"] = self.extras

		"""If tree has a parent, and its class does not match
		this branch, serialise ref to class of this branch
		alongside it
		"""
		if self.parent:

			if self.parent.__class__ != self.__class__:
				objData = saveObjectClass(self)
				serial["objData"] = objData
				# it now costs exactly one extra line to define the child class
				# it's worth it to avoid the pain of adaptive definition
		else:
			""" If tree does not have a parent, insert a data format
			version number at root of dictionary
			In future this will be handled by the FormatManager
			"""
			if self.rootData():
				serial["?ROOT_DATA"] = self.rootData()
			serial["?FORMAT_VERSION"] = 0

		# always returns dict
		return serial

	def display(self):
		seq = pprint.pformat( self.serialise() )
		return seq

	@staticmethod
	def _setTreeValue(tree, value):
		""" stub for setting tree values asynchronously """
		tree.value = value