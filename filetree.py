

from tree import Tree
from collections import namedtuple


class FileTree(Tree):
	""" tree object for interfacing with files on disk
	read only for now

	>>>fileTreeA = FileTree("F:/root_dir")
	>>>childDir = fileTreeA("assets")
	but what if there is both assets folder and assets.txt?
	call always looks for folder, get looks for files
	if there is both assets.txt and assets.json?
	up to caller to specify
	>>>firstFile = fileTreeA["assets"]
	get always returns list of files matching lookup
	>>>textFile = fileTreeA["assets.txt"]
	probably only returns list of length 1
	goes without saying that having double names should be avoided anyway
	>>>newDir = fileTreeA("crazyPath")
	newDir is None - by default nothing is created
	>>>realNewDir = fileTreeA("crazyPath", create=True)
	F:/root_dir/crazyPath folder is created

	"""

	def __init__(self, rootDir):
		""":param rootDir : path of root directory for tree """
		super(FileTree, self).__init__(name="ROOT", val=rootDir)

	@property
	def rootPath(self):
		return self.root.value


	def goHere(self):
		""" moves console execution into this folder"""



