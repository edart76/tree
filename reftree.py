from main import Tree

class RefTree(Tree):
	"""
	a read-only representation of a tree on disk somewhere
	may still be reparented

	I don't know how this would overlap with the proxy tree

	"""
