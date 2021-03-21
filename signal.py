
from sys import version_info


import inspect
from weakref import WeakSet, WeakKeyDictionary
from collections import deque
from functools import partial


class Signal(object):
	""" basic signal emitter
	fired signals are added to this object's calling frame -
	if this becomes excessive, this
	also includes mode to add function calls to queue
	instead of directly firing connnected functions

	queue support not complete yet, as nothing I use needs it.
	"""
	
	queues = {"default" : deque()}
	
	def __init__(self, queue="", useQueue=False):
		""":param queue : name of queue to use, or external queue object """
		self._functions = WeakSet()
		self._methods = WeakKeyDictionary()

		# is signal active
		self._active = True

		# event queue support
		self._useQueue = useQueue
		self._queue = queue or "default"

	def __call__(self, *args, **kwargs):

		if not self._active:
			return

		queue = self.getQueue()
		# Call handler functions
		for func in self._functions:
			if self._useQueue:
				queue.append(partial(func, *args, **kwargs))
			else:
				func(*args, **kwargs)

		# Call handler methods
		for obj, funcs in self._methods.items():
			for func in funcs:
				if self._useQueue:
					queue.append(partial(func, obj, *args, **kwargs))
				else:
					func(obj, *args, **kwargs)

	def activate(self):
		self._active = True
	def mute(self):
		self._active = False

	def getQueue(self, name="default", create=True):
		"""return one of the event queues attended by signal objects"""
		name = name or self._queue or "default"
		if not name in self.queues and create:
			self.queues[name] = deque()
		return self.queues[name]

	def setQueue(self, queueName):
		""" set signal to use given queue """
		self._queue = queueName

	def emit(self, *args, **kwargs):
		""" brings this object up to rough parity with qt signals """
		self(*args, **kwargs)

	def connect(self, slot):
		if inspect.ismethod(slot):
			if slot.__self__ not in self._methods:
				self._methods[slot.__self__] = set()

			self._methods[slot.__self__].add(slot.__func__)
		else:
			self._functions.add(slot)

	def disconnect(self, slot):
		if inspect.ismethod(slot):
			if slot.__self__ in self._methods:
				self._methods[slot.__self__].remove(slot.__func__)
		else:
			if slot in self._functions:
				self._functions.remove(slot)

	def clear(self):
		self._functions.clear()
		self._methods.clear()