""" thoughts on the true philosophical nature of trees """

import weakref
import networkx

"""
consider that instancing objects creates effectively a new dependency graph
over them, as an instance can never instance itself -
if all instances can only have one source object, we create another tree,
in another dimension across the same branches

the tree is already a special case of the graph

so the ultimate general case would be a pool of nodes,
and a set of edges for each dimension present in the graph - 
only the nodes actually exist, the graph can be drawn over them 
however you want

"""

class Graph(object):

	def __init__(self):
		self.nodes = []
		self.edges = []


class Node(object):

	def __init__(self, name=None):
		self.name = name
		self.connections = {}

class TreeNode(Node):
	""" more specific node for tree structures
	not ENTIRELY sure if this should be the final tree node class,
	or if there should be additional layers
	"""
	def __init__(self, name=None, value=None):
		pass


