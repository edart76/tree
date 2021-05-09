
"""
Consider the following common problem:
- You start work on stateful system (for example, a tree-like data structure)
- You release it, it gets used in production,
	many files are saved using it
- All is well
- You realise you want / need to make changes to the way it stores its
	data, but you can't break compatibility with the thousands of files
	already out there in the wild.

The ideal is to avoid the above situation, but nobody is perfect,
    or clairvoyant.
One solution is to work out what 'version' of the data format is being
	used purely by the structure of the data itself, and then account
	for that with sequential if-checks in the parsing system - while there
	are no good solutions to this problem, this strikes me as the most not good.

A better solution would be to accept the above as inevitability,
	and consider it in the system from the beginning.


Manager object provides decorator methods to mark client
io functions as version-specific


class DataStructure(object):
	formatManager = FormatManager(
		versionReadKey=lambda x: x["?VERSION_FORMAT"],
		versionWriteKey=lambda x, val: x["?VERSION_FORMAT"] = val,
	)

	@formatManager.serialiser(0)
	def writeMyOldFormat(self):
		do stuff
		return {"data" : 773}

	@formatManager.serialiser(1)
	def writeMyNewFormat(self):
		do different stuff
		return {"goss" : {"data" : 773}}

	# main method
	def saveData(self):
		#data = formatManager.serialise()
		serialiseFn = formatManager.latestSerialiser
		data = serialiseFn(arg1, kwarg3=4)


"""

import os, sys, json, fnmatch
from types import FunctionType, LambdaType
from functools import wraps, partial

class FormatManager(object):

	def __init__(self,
	             versionReadKey:(str, FunctionType),
	             versionWriteKey:(str, FunctionType)):
		"""
		Object to make changing serialised data formats
		easier to work with

		:param versionReadKey : string key or function
		to evaluate on given serialised data to get
		 the format version of that data
		:param versionWriteKey : string key or function
		to save the format version to a serialised data structure
		----recommend to use simple string
		or int keys for both of these----
		"""

		self.readKey = versionReadKey
		self.writeKey = versionWriteKey

		self.serialiserFns = {}
		self.deserialiserFns = {}

	def serialiser(self, version:(int)):
		"""Decorator function for serialising
		Decorator adds given format version to data
		after wrapped function acts
		"""
		def fnWrapper(fn): # receives function object
			@wraps(fn)
			def fnCallWrapper(*args, **kwargs): # receives function call args
				result = fn(*args, **kwargs)
				# add format verion tag to data
				if isinstance(self.writeKey, (str, int)):
					result[self.writeKey] = version
				elif isinstance(self.writeKey, (function, LambdaType)):
					self.writeKey(result, version)
				return result

			# add wrapped function to serialisers
			self.serialiserFns[version] = fnCallWrapper
			return fnCallWrapper
		return fnWrapper


	def deserialiser(self, version:(int)):
		"""Decorator function for loading object back
		from serialised data#
		Decorator has no active effect, just used to index function"""
		def fnWrapper(fn):
			@wraps(fn)
			def fnCallWrapper(*args, **kwargs):
				result = fn(*args, **kwargs)
				return result,
			# add wrapped function to deserialisers
			self.deserialiserFns[version] = fnCallWrapper
			return fnCallWrapper
		return fnWrapper

	@property
	def latestSerialiser(self):
		"""get most up to date serialiser function"""
		return self.serialiserFns[max(self.serialiserFns.keys())]
	@property
	def latestDeserialiser(self):
		"""get most up to date deserialiser function"""
		return self.deserialiserFns[max(self.deserialiserFns.keys())]

	def getDataVersion(self, data):
		""" retrieve the int version used in a block of data """
		if isinstance(self.readKey, (str, int)):
			return data[self.readKey]
		elif isinstance(self.readKey, (function, LambdaType)):
			return self.readKey(data)


	# def serialise(self): # too opaque
	# 	"""Storing functions is simple for now,
	# 	maybe store argspec or partial alongside each one
	# 	"""



