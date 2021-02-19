
""" collection of tree and tree modules """

from tree.core import TreeBase

class Tree(TreeBase):
	pass

	@classmethod
	def _defaultCls(cls):
		return Tree