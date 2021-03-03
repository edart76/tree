
""" delta extraction for primitive objects and tree """

from six import iteritems
import functools

from collections import namedtuple

import difflib

import uuid
import proxy

class ListDelta(object):
	""" atomic transform for lists
	 indices still dicy """
	replaceData = namedtuple("replaceData", ["start", "end", "data"])
	insertData = namedtuple("insertData", ["index", "data"])
	deleteData = namedtuple("deleteData", ["start", "end", "data"])

	@staticmethod
	def complexToId(sequence, idMap=None):
		""" given a sequence, convert all unhashable objects
		to their ids, and store these in a map """
		idMap = idMap or {}
		copySeq = list(sequence) # may not be necessary in the end
		for i, val in enumerate(sequence):
			try:
				hash(val)
			except:
				# check if already exists in map
				if val in idMap.values():
					tag = [k for k, v in iteritems(idMap)
					       if v is val][0]
				else:
					tag = uuid.uuid1()
				copySeq[i] = tag
				idMap[tag] = val
		return (copySeq, idMap)

	@staticmethod
	def allToId(sequence):
		""" because of shared hashes, and especially
		(a IS b) for equal strings, need to first assign
		EVERY element a uuid, regardless of repeat """
		idMap = {}
		copySeq = list(sequence)
		for i, val in enumerate(sequence):
			tag = uuid.uuid1()
			idMap[tag] = val
			copySeq[i] = tag
		return copySeq, idMap

	@staticmethod
	def idToAll(idMap, sequence):
		copySeq = list(sequence)
		for i, tag in enumerate(sequence):
			copySeq[i] = idMap[tag]
		return copySeq

	@staticmethod
	def idToComplex(idMap, sequence):
		copySeq = list(sequence)
		for i, tag in enumerate(sequence):
			if tag in idMap:
				copySeq[i] = idMap[ sequence[i] ]
		return sequence

	@classmethod
	def extractDeltas(cls, seqA, seqB):
		""" ignore complex objects for now """
		# hashA, mapA = cls.allToId(seqA)
		# hashB, mapB = cls.allToId(seqB)

		# flatten complex objects
		flatA, idMap = cls.complexToId(seqA)
		flatB, idMap = cls.complexToId(seqB, idMap)

		data = []
		result = difflib.SequenceMatcher(
			isjunk=None,
			a=flatA,
			b=flatB,
			autojunk=False).get_opcodes()

		# having used flattened sequences for extraction,
		# can we then use rich objects in actual deltas?
		for op, aStartIndex, aEndIndex, \
			bStartIndex, bEndIndex in result:
			if op == "replace" : # can do dicts for portability
				data.append(cls.replaceData(
					start=aStartIndex,
					end=aEndIndex,
				    data=seqB[ bStartIndex : bEndIndex ]))
			elif op == "insert" :
				data.append(cls.insertData(
					index=aStartIndex,
					data=seqB[bStartIndex: bEndIndex]))
			elif op == "delete" :
				data.append(cls.deleteData(
					start=aStartIndex, end=aEndIndex,
					data=seqA[aStartIndex:aEndIndex]))
		#print(data)
		return data

	@classmethod
	def applyDelta(cls, data, baseSeq=None):
		"""	given a single diff data tuple, apply it to the sequence
		and return it
		:param data: diff data namedtuple
		:param baseSeq: list
		:return:
		"""

		if type(data) == cls.replaceData:
			baseSeq = baseSeq[:data.start] + data.data + \
			          baseSeq[data.end:]
		elif type(data) == cls.insertData:
			print("inserting")
			baseSeq = baseSeq[:data.index] + data.data + baseSeq[data.index:]
		elif type(data) == cls.deleteData:
			baseSeq = baseSeq[:data.start] + baseSeq[data.end:]
		# print("newSeq ", baseSeq)
		return baseSeq



class DictDelta(object):
	""" atomic transform for dicts
	order preservation is only as good as
	the list delta system
	"""
	replaceOp = namedtuple("replaceData", ["key", "data"])
	insertOp = namedtuple("insertData", ["key", "data"])
	deleteOp = namedtuple("deleteData", ["key"])

	@classmethod
	def extractDeltas(cls, dA, dB):
		""" ignore complex objects for now
		keys are most important"""
		ops = []
		indexMap = [] # ???????

		for i, (kA, vA) in enumerate(iteritems(dA)):
			if not kA in dB:
				ops.append(cls.deleteOp(kA))
				indexMap.append( (-1, kA))
				continue
			if vA != dB[kA]:
				ops.append(cls.replaceOp(key=kA, data=dB[kA]))
			indexMap.append((i, kA)) # ???????

		for i, (kB, vB) in enumerate(iteritems(dB)):
			if not kB in dA:
				ops.append(cls.insertOp(key=kB, data=vB))
		return ops


	@classmethod
	def applyDelta(cls, op, baseMap=None):
		"""	given a single diff data tuple, apply it to the map
		"""

		if type(op) == cls.deleteOp:
			baseMap.pop(op.key)
		elif isinstance(op, (cls.replaceOp, cls.insertOp)):
			baseMap[op.key] = op.data


