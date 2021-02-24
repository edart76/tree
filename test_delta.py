
from __future__ import print_function
from sys import version_info
if version_info[0] < 3:
	pyTwo = True
	#import unittest2 as unittest
	import unittest

else:
	pyTwo = False
	import unittest

import pprint

from tree import Tree, Signal
from delta import Delta, DictDelta, ListDelta, TreeDelta
from proxy import Proxy


def makeTestObjects():
	tempTree = Tree(name="testRoot", val="tree root")
	tempTree("branchA").value = "first branch"
	tempTree("branchA")("leafA").value = "first leaf"
	tempTree("branchB").value = 2

	baseDict = {"a" : "b", 5 : 65}

	baseList = ["a", "c", "b", 49494, "e"]

	return {"tree" : tempTree, "baseDict" : baseDict,
	        "list" : baseList
	        }

class DebugProxy(Proxy):

	# def __init__(self, obj):
	# 	print("super {}".format(super(DebugProxy, self)))
	# 	super(DebugProxy, self).__init__(obj)

	def __eq__(self, other):
		# print("super {}".format(super(DebugProxy, self)))
		#result = super(DebugProxy, self).__eq__(other)

		print("other", other, type(other))
		result = self._proxyObj.__eq__(other)
		# does this work
		#result = other.__eq__(self._proxyObj)
		print("debug eq {} == {} - {}".format(type(self).__name__,
		                                      type(other).__name__,
		                                      result))
		print(type(result))
		return result

# print( {} == {})

class TestProxy(unittest.TestCase):
	""" test for base proxying of objects """

	def setUp(self):
		""" construct basic objects """
		self.baseDict = makeTestObjects()["baseDict"]

	def test_baseProxy(self):
		""" test that tree objects find their root properly """
		p = Proxy(self.baseDict)
		self.assertEqual(self.baseDict, p, msg="""
		proxy object is not equal to base""")
		self.assertIsNot(self.baseDict, p, msg="""
		proxy object IS base""")

	def test_proxyTyping(self):
		""" test that object class is properly mimicked """
		p = Proxy(self.baseDict)
		self.assertIsInstance(p, Proxy, msg="Proxy is not a proxy instance")
		self.assertIsInstance(p, dict, msg="Proxy is not an instance of dict")
		self.assertIsInstance({}, type(p),
		    msg="dict is not an instance of generated proxy class")

	def test_proxySuper(self):
		pass

	def test_proxyList(self):
		baseList = ["test"]
		pList = DebugProxy(baseList)
		newList = ["new"]

		self.assertEqual(pList[0], "test")

		# both = newList + pList
		# print(both)




	def test_proxyEq(self):
		# p = Proxy(self.baseDict)
		p = DebugProxy(self.baseDict)
		self.assertEqual(p, self.baseDict)
		self.assertEqual(self.baseDict, p)

		# pp = Proxy(p)
		pp = DebugProxy(p)
		self.assertEqual(pp, self.baseDict)
		self.assertEqual(self.baseDict, pp)

		# I don't know how proxies should act with other proxies
		# self.assertEqual(pp, p)
		# self.assertEqual(p, pp)


class TestDeltaList(unittest.TestCase):

	def setUp(self):
		self.baseList = makeTestObjects()["list"]

	def test_baseListDelta(self):
		d = ListDelta(self.baseList)

		self.assertEqual(d, self.baseList)

		d.append("appItem")

		self.assertEqual(d, self.baseList + ["appItem"])
		self.assertFalse(d == self.baseList)

		self.baseList.insert(1, "insItem")

		self.assertEqual(d, d._product())

		print("")

		print(d._product())
		print(self.baseList)
		print(d, "t")
		print(d._product())




if __name__ == '__main__':
	unittest.main()



