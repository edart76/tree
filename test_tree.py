
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

tempTree = Tree(name="testRoot", val="tree root")
tempTree("branchA").value = "first branch"
tempTree("branchA")("leafA").value = "first leaf"
tempTree("branchB").value = 2

class TestMainTree(unittest.TestCase):
	""" test for main tree interface methods """

	def setUp(self):
		""" construct a basic test tree """

		self.tree = Tree(name="testRoot", val="tree root")
		self.tree("branchA").value = "first branch"
		self.tree("branchA")("leafA").value = "first leaf"
		self.tree("branchB").value = 2

		self.serialisedTruth = {'?VALUE': 'tree root', '?CHILDREN': [{'?VALUE': 'first branch', '?CHILDREN': [{'?VALUE': 'first leaf', '?NAME': 'leafA'}], '?NAME': 'branchA'}, {'?VALUE': 2, '?NAME': 'branchB'}], '?NAME': 'testRoot'}

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
		self.assertIs(self.tree(["branchA", "leafA"]),
		              self.tree("branchA")("leafA"),
		              msg="error in list retrieval")


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
		newCopy = newBranch.__copy__()
		self.assertEqual(newBranch, newCopy,
		                 msg="branch and its shallow copy are not equal")
		self.assertFalse(newBranch is newCopy,
		                 msg="branch IS its copy")
		self.assertTrue(newBranch in self.tree("branchA"),
		                msg="tree does not contain its branch")
		self.assertFalse(newCopy in self.tree("branchA"),
		                 msg="tree contains copy of its branch")



	def test_treeSerialisation(self):
		""" test serialising tree to dict
		should get more advanced testing here, serialisation
		needs to support more stuff """

		#pprint.pprint(self.tree.serialise())
		#print(self.tree.serialise())

		self.assertEqual(self.tree.serialise(), self.serialisedTruth,
		                 msg="mismatch in serialised data")

	def test_treeRegeneration(self):
		""" test regeneration from dict """
		self.assertEqual(Tree.fromDict(self.tree.serialise()), self.tree)



if __name__ == '__main__':

	unittest.main()



