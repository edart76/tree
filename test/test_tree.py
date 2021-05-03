
from __future__ import print_function
from sys import version_info
import os
if version_info[0] < 3:
	pyTwo = True
	#import unittest2 as unittest
	import unittest

else:
	pyTwo = False
	import unittest

import pprint

from tree import Tree, Signal

tempTree = Tree(name="testRoot", val="tree root")
tempTree("branchA").value = "first branch"
tempTree("branchA")("leafA").value = "first leaf"
tempTree("branchB").value = 2

midTree = tempTree.__deepcopy__()
midTree("branchA")("listLeaf").value = ["a", "b", 10, "d"]
midTree("dictBranch").value = {"key" : "value", "oh" : {"baby" : 3}}

jsonOutPath = os.path.sep.join(
	os.path.split(__file__ )[:-1]) + "testLog.json"

class CustomTreeType(Tree):
	branchesInherit = True
	pass


class TestMainTree(unittest.TestCase):
	""" test for main tree interface methods """

	def setUp(self):
		""" construct a basic test tree """

		self.tree = Tree(name="testRoot", val="tree root")
		# self.tree.debugOn = True
		self.tree("branchA").value = "first branch"
		self.tree("branchA")("leafA").value = "first leaf"
		self.tree("branchB").value = 2

		self.serialisedTruth = {'?VALUE': 'tree root', '?CHILDREN': [{'?VALUE': 'first branch', '?CHILDREN': [{'?VALUE': 'first leaf', '?NAME': 'leafA'}], '?NAME': 'branchA'}, {'?VALUE': 2, '?NAME': 'branchB'}], '?NAME': 'testRoot',
		                        '?FORMAT_VERSION': 0,}

	def test_treeRoot(self):
		""" test that tree objects find their root properly """
		self.assertIs( self.tree.root, self.tree,
		                  msg="tree root is not itself")
		self.assertIs(self.tree("branchA").root, self.tree,
		                  msg="tree branch finds incorrect root of "
		                      "{}".format(self.tree))
		self.assertIs(self.tree("branchA")("leafA").root, self.tree,
		                  msg="tree leaf finds incorrect root of "
		                      "{}".format(self.tree))

	def test_treeRetrieval(self):
		""" test retrieving values and branches
		 using different methods """
		# token retrieval
		self.assertIs(self.tree("branchA", "leafA"),
		              self.tree("branchA")("leafA"),
		              msg="error in token retrieval")
		# sequence retrieval
		# self.assertIs(self.tree(["branchA", "leafA"]),
		#               self.tree("branchA")("leafA"),
		#               msg="error in list retrieval")
		# NOT USED YET

		# string retrieval
		self.assertEqual( self.tree(
			self.tree.sep.join(["branchA", "leafA"])),
			self.tree("branchA")("leafA"),
		                 msg="string address error")

		# parent retrieval
		self.assertEqual( self.tree("branchA", "leafA", "superleafA"),
		                  self.tree("branchA", "leafA", "superleafA",
		                            "^", "^", "leafA", "superleafA"))


	def test_treeAddresses(self):
		""" test address system
		check equivalence of list and string formats """
		# sequence address
		self.assertEqual(self.tree("branchA")("leafA").address,
		                  ["branchA", "leafA"],
		                  msg="address sequence error")
		# string address
		self.assertEqual(self.tree("branchA")("leafA").stringAddress(),
		      self.tree.sep.join(["branchA", "leafA"]),
		                 msg="string address error")


	def test_treeInsertion(self):
		""" test inserting new branch"""
		newBranch = Tree(name="newBranch", val=69)
		self.tree("branchA")("leafA").addChild(newBranch)
		self.assertIs(self.tree("branchA")("leafA")("newBranch"),
		              newBranch)

	def test_treeEquality(self):
		""" testing distinction between identity and equality """
		newBranch = self.tree("branchA", "new")
		self.assertTrue(newBranch in self.tree("branchA"),
		                msg="Tree does not contain its branch")
		newCopy = newBranch.__copy__()
		self.assertEqual(newBranch, newCopy,
		                 msg="branch and its shallow copy are not equal")
		self.assertFalse(newBranch is newCopy,
		                 msg="branch IS its copy")
		# self.assertTrue(newBranch is self.tree("branchA"),
		#                 msg="tree does not contain its branch")
		self.assertFalse(newCopy is self.tree("branchA"),
		                 msg="tree contains copy of its branch")



	def test_treeSerialisation(self):
		""" test serialising tree to dict
		should get more advanced testing here, serialisation
		needs to support more stuff """

		self.assertEqual(self.tree.serialise(), self.serialisedTruth,
		                 msg="mismatch in serialised data")
		restoreTree = self.tree.fromDict(self.tree.serialise())
		self.assertEqual(self.tree, restoreTree,
		                 msg="restored tree not equal to its source")


	def test_treeRegeneration(self):
		""" test regeneration from dict """
		self.assertEqual(Tree.fromDict(self.tree.serialise()), self.tree)

	def test_treeTyping(self):
		""" test custom tree types in contiguous hierarchy """
		self.tree.addChild(
			CustomTreeType("customBranch", val=34535))
		restoreTree = self.tree.fromDict(self.tree.serialise())
		self.assertEqual(self.tree, restoreTree,
		                 msg="restored custom tree not equal to its source")
		self.assertIs(type(restoreTree("customBranch")), CustomTreeType,
		                 msg="restored custom type not equal to its source")



if __name__ == '__main__':

	unittest.main()



