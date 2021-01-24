

from sys import version_info
if version_info[0] < 3:
	pyTwo = True
	import unittest2 as unittest

else:
	pyTwo = False
	import unittest

from tree import Tree, Signal


class TestMainTree(unittest.TestCase):
	""" test for main tree interface methods """

	def setUp(self):
		""" construct a basic test tree """

		self.tree = Tree(name="testRoot", val="tree root")
		self.tree("branchA").value = "first branch"
		self.tree("branchA")("leafA").value = "first leaf"
		self.tree("branchB").value = 2

	def test_treeRoot(self):
		""" test that tree objects find their root properly """
		self.assertEqual( self.tree.root, self.tree,
		                  msg="tree root is not itself")
		self.assertEquals(self.tree("branchA").root, self.tree,
		                  msg="tree branch finds incorrect root of "
		                      "{}".format(self.tree))
		self.assertEquals(self.tree("branchA")("leafA").root, self.tree,
		                  msg="tree leaf finds incorrect root of "
		                      "{}".format(self.tree))

	def test_treeAddresses(self):
		""" test address system
		check equivalence of list and string formats """

	def test_treeRetrieval(self):
		""" test retrieving values """

	def test_treeInsertion(self):
		""" test inserting new branch"""

		



if __name__ == '__main__':
	unittest.main()



