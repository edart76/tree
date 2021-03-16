from weakref import WeakSet
from abc import ABC
from functools import wraps
from types import FunctionType, MethodType, BuiltinFunctionType



class Proxy(ABC):
	""" Transparent proxy for most objects
	code recipe 496741
	further modifications by ya boi

	should function roughly as a mixin

	__call__, then __new__, then __init__

	"""
	#__slots__ = ["_obj", "__weakref__"]
	_class_proxy_cache = {} # { class : { class cache } }
	_proxyAttrs = ("_proxyObjRef", "_proxyObj", "_proxyChildren")
	_proxyObjKey = "_proxyObjRef" # attribute pointing to object
	# _methodHooks = {}

	def __init__(self, obj):
		#self._proxyObjRef = obj # set already in __new__
		self._proxyChildren = WeakSet() # make this lazy if needed

	@property
	def _proxyObj(self):
		#return self._returnProxy()
		return object.__getattribute__(self, self._proxyObjKey)
	@_proxyObj.setter
	def _proxyObj(self, val):
		object.__setattr__(self, self._proxyObjKey, val)

	def _returnProxy(self):
		""" hook for extending proxy behaviour
		prefer overriding this over properties"""
		return object.__getattribute__(self, self._proxyObjKey)

	# proxying (special cases)
	# def __getattribute__(self, name):
	def __getattr__(self, name):

		try: # look up attribute on proxy class first
			return object.__getattribute__(self, name)
		except:
			obj = object.__getattribute__(self, "_proxyObjRef")

			#return getattr( self._proxyObj, name)
			return getattr( obj, name)

	def __delattr__(self, name):
		delattr(object.__getattribute__(self, self._proxyObjKey), name)

	def __setattr__(self, name, value):
		try:
			if name in self.__pclass__._proxyAttrs:
				object.__setattr__(self, name, value)
			else:
				setattr(self._proxyObj, name, value)
		except Exception as e:
			#print("p attrs {}".format(self.__pclass__._proxyAttrs))
			print("error name {}, value {}".format(name, value))
			print("type name ", type(name))
			raise e


	def __nonzero__(self):
		return bool(self._proxyObj)

	def __str__(self):
		return str(self._proxyObj)

	def __repr__(self):
		return repr(self._proxyObj)

	# factories
	_special_names = [
		'__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
		'__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
		'__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
		'__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
		'__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
		'__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
		'__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
		'__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
		'__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
		'__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__',
		'__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
		'__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
		'__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
		'__truediv__', '__xor__', 'next',
	]

	@classmethod
	def _create_class_proxy(cls, targetCls):
		"""creates a proxy for the given class

		CONSIDER -
		how to handle super() calls from within functions?

		two options: the all-singing-all-dancing way would be to create
		TWO proxy classes per target class - one template class to hold
		the base supplanted methods, and a child class inheriting from
		it to hold overrides.

		we could also introduce a 'self.psuper()' thing to represent
		the base proxy behaviour? somehow?

		or the correct way - if you're overriding magic methods,
		you can handle a couple of extra lines to access the proxy
		object directly, as one would hope you know what you're doing

		"""
		# combine declared proxy attributes
		# cls._proxyAttrs = set(cls._proxyAttrs)
		allProxyAttrs = set(cls._proxyAttrs)
		for base in cls.__mro__:
			#if base in (object, ABC): break
			if getattr(base, "_proxyAttrs", None):
				#print(base.__name__, base._proxyAttrs)
				#cls._proxyAttrs.update(base._proxyAttrs)
				allProxyAttrs.update(base._proxyAttrs)

		def make_method(name):
			# print("wrap {} for class {}".format(name, targetCls))
			# works even for builtins
			def method(self, *args, **kw):
				#print("m " + name)
				return getattr(
					self._proxyObj,
					name)(*args, **kw)
			return method

		namespace = {}
		namespace["_proxyAttrs"] = allProxyAttrs
		for name in cls._special_names:
			# do not override methods if they appear in class
			if hasattr(targetCls, name) \
					and not name in cls.__dict__:
				namespace[name] = make_method(name)
		newCls = type("{}({})".format(cls.__name__, targetCls.__name__),
		              (cls,), namespace)
		newCls.register(targetCls)
		print("new cls pattrs ", newCls._proxyAttrs)

		return newCls

	# @property
	# def __class__(self):
	# 	# supplant __class__ on newCls to return target
	# 	# see the research for less weird options
	# 	try: # should work for proxies of proxies
	# 		return self._proxyObj.__class__
	# 	except:
	# 		return type(self._proxyObj)

	@property
	def __pclass__(self):
		"""proxy class
		as __class__ is taken, this is to allow idoms like
		self.__class__.__name__ to continue with the minimum
		disruption """
		return type(self)

	@property
	def _parentclass(self):
		""" yes this is very confusing with __pclass__
		exists as super() apparently isn't great at handling
		the deferred lookup? idk """


	def __new__(cls, obj, *args, **kwargs):
		"""
        creates a proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        base Proxy class holds master dict

        proxying a proxy will create a new class for each layer
        and set of parents - this is not ideal, but hasn't hurt yet

        """
		# looks up type-specific proxy class
		cache = Proxy.__dict__["_class_proxy_cache"]
		try:
			genClass = cache[cls][type(obj)]
		except KeyError:
			genClass = cls._create_class_proxy(type(obj))
			cache[cls] = { type(obj) : genClass }

		# create new proxy instance of type-specific proxy class
		ins = object.__new__(genClass)

		ins.__dict__[cls._proxyObjKey] = obj

		# run init on created instance
		genClass.__init__(ins, obj, *args, **kwargs)
		return ins