
"""
Fractal tree-like data structure,
supporting sequence and string lookup,
with each object having name and value.

Please depend on / import only the objects included
in this init file. This system is still under development,
and only types included here are considered forwards compatible.

"""


from .main import Tree
from .signal import Signal
#from dev.tree2 import Graph
__all__ = [
	"Tree",
	"Signal",
	# "Graph",
]

