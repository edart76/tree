
""" python functions used in tree and associated objects"""
import importlib
import string
from sys import version_info

from main import uniqueSign, basestring

if version_info[0] < 3: # hacky 2-3 compatibility
	pyTwo = False
	basestring = str
else:
	pyTwo = True

import inspect


def trimArgsKwargs(fn, givenArgs, givenKwargs=None):
	""" given function, and tuple and dict of args and kwargs,
	trim args to accepted length, and remove all but given kwargs from dict
	for use in signals - some functions just need to trigger
	on specific signals, while others may need more detail information passed
	to them
	"""
	argSpec = inspect.getfullargspec(fn)
	if argSpec.varargs:
		args = list(givenArgs)
	else:
		givenArgs = list(givenArgs)
		args = givenArgs[:min(len(argSpec.args), len(givenArgs))]

	if argSpec.varkw:
		kwargs = givenKwargs
	else:
		kwargs = {k : v for k, v in givenKwargs.items() if
		          k in argSpec.kwonlyargs}
	return (args, kwargs)


def incrementName(name, currentNames=None):
	"""checks if name is already in children, returns valid one"""
	if currentNames and name not in currentNames:
		return name
	if name[-1].isdigit(): # increment digit like basic bitch
		new = int(name[-1]) + 1
		return name[:-1] + str(new)
	if name[-1] in string.ascii_uppercase: # ends with capital letter
		if name[-1] == "Z": # start over
			name += "A"
		else: # increment with letter, not number
			index = string.ascii_uppercase.find(name[-1])
			name = name[:-1] + string.ascii_uppercase[index+1]
	else: # ends with lowerCase letter
		name += "B"

	# check if name already taken
	if currentNames and name in currentNames:
		return incrementName(name, currentNames)
	return name


def safeLoadModule(mod, logFunction=None):
	"""takes string name of module
	"""
	logFunction = logFunction or print
	module = None
	try:
		module = importlib.import_module(mod)
	except ImportError() as e:
		logFunction("ERROR in loading module {}".format(mod))
		logFunction("error is {}".format(str(e)))
	return module


def saveObjectClass(obj, regenFunc="fromDict", relative=True, uniqueKey=True,
					legacy=False):
	""" saves a module and class reference for any object
	if relative, will return path from root folder"""
	keys = [ "NAME", "CLASS", "MODULE", "regenFn" ]
	if uniqueKey: # not always necessary
		for i in range(len(keys)): keys[i] = "?" + keys[i]

	#path = convertRootPath(obj.__class__.__module__, toRelative=relative)
	path = obj.__class__.__module__
	if legacy: # old inefficient dict method
		return {
			keys[0]: obj.__name__,
			keys[1]: obj.__class__.__name__,
			keys[2]: path,
			keys[3]: regenFunc
		}
	data = uniqueSign.join([obj.__class__.__name__, path])
	return data


def loadObjectClass(objData):
	""" recreates a class object from any known module """
	if isinstance(objData, dict):
		for i in ("?MODULE", "?CLASS"):
			if not objData.get(i):
				print("objectData {} has no key {}, cannot reload class".format(objData, i))
				return None
		path = objData["?MODULE"]
		className = objData["?CLASS"]

	elif isinstance(objData, (tuple, list)):
		# sequence [ class, modulepath, regenFn ]
		path = objData[1]
		className = objData[0]
	elif isinstance(objData, basestring):
		className, path = objData.split(uniqueSign)

	#module = convertRootPath( path, toAbsolute=True)
	module = path
	loadedModule = safeLoadModule(module)
	try:
		newClass = getattr(loadedModule, className)
		return newClass
	except Exception as e:
		print("ERROR in reloading class {} from module {}")
		print("has it moved, or module files been shifted?")
		print( "error is {}".format(str(e)) )
		return None