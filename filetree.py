


from collections import namedtuple
import os, shutil
from os import PathLike


from main import Tree

class FileTree(Tree, PathLike):
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

	def __init__(self, dirPath):
		""":param dirPath : path of root directory for tree """
		super(FileTree, self).__init__(name="ROOT", val=dirPath)

	def __fspath__(self):
		""" return the absolute path to this branch """
		return os.path.join(self.rootPath, self.address)

	@property
	def rootPath(self):
		return self.root.value


	def goHere(self):
		""" moves console execution into this folder"""



