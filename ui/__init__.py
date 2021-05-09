
import os.path

# replace with filetree once ready
RESOURCE_DIR = os.sep.join([
	os.sep.join(os.path.split(__file__)[:-1]), "res/"])

from .widget import TreeWidget
