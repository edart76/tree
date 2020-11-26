# tree
Tree data structure.

Single Tree() object. No distinction between branches and leaves - each object may have a value and / or define its own branches.

# Includes :
 - tree.py : base Tree() object, and helper functions for serialisation / deserialisation.
 - delta.py : mechanism for creating live "proxies" or references to primitive and Tree objects, tracking changes to the reference as deltas atop the original object. In this way an object's contents can be overridden in the same way as object-oriented inheritance.
 - filetree.py : experiment for applying tree syntax to navigating filesystems.

# Motivation
 - I needed a single base class for data structures, with consistent access and serialisation methods.
 - Existing solutions (see below) were either too complex or too simple (I needed to store a small amount of metadata in each node object, which the defaultDict() method doesn't support).
 - Existing solutions did not supply the live-inheritance / override / referencing system used to track tree deltas.


# Similar projects for comparison
data-tree : https://pypi.org/project/data-tree/
 - focus on optimisation
 - *interesting* naming convention for functions and arguments
anytree : anytree.readthedocs.io/en/latest/intro.html
 - discrete classes of tree nodes
 - provides mixin for any python object to be a direct node in the tree, instead of just referenced by a node
 - quite class-heavy
 - fun methods for pretty-printing tree contents
Disney's dRig : https://media.disneyanimation.com/uploads/production/publication_asset/7/asset/dRigTalk_v05.pdf
 - allows live inheritance and overrides
