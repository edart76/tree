
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
	        }

class DebugProxy(Proxy):

	# def __init__(self, obj):
	# 	print("super {}".format(super(DebugProxy, self)))
	# 	super(DebugProxy, self).__init__(obj)

	def __eq__(self, other):
		# print("super {}".format(super(DebugProxy, self)))
		#result = super(DebugProxy, self).__eq__(other)
		result = self._proxyObj.__eq__(other)
		print("debug eq {} == {} - {}".format(type(self).__name__,
		                                      type(other).__name__,
		                                      result))
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

		# super does work but I can't work out how to test it properly
		# from outside the class
		# s = super(type(p))
		# print(s.__self__)
		# print(s.__self_class__)
		# print(s.__thisclass__)
		#
		# print(type(super(type(p))))
		# # self.assertEqual(super(type(p)).__dict__, Proxy.__dict__)
		# self.assertEqual(super(type(p)), Proxy)

	def test_proxyEq(self):
		p = Proxy(self.baseDict)
		self.assertEqual(p, self.baseDict)
		self.assertEqual(self.baseDict, p)

		pp = Proxy(p)
		self.assertEqual(pp, self.baseDict)
		self.assertEqual(self.baseDict, pp)

		self.assertEqual(pp, p)
		self.assertEqual(p, pp)

	# def test_proxyLayering(self):
	# 	p = DebugProxy(self.baseDict)
	# 	pp = DebugProxy(p)
	# 	self.assertIsInstance(pp, Proxy)
	# 	self.assertIsInstance(pp, dict)
	#
	# 	# print(type(p))
	# 	# print(type(pp))
	# 	# print(pp == self.baseDict)
	# 	# print(p == pp)
	#
	#
	# 	self.assertEqual(pp, p)
	# 	self.assertEqual(pp, self.baseDict)




if __name__ == '__main__':
	unittest.main()



