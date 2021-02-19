

""" goal is a transparent wrapper that properly
spoofs instance and subclass checking, while avoiding
inits and new on the target class """

import copy
from collections import OrderedDict
import inspect
from weakref import WeakSet
from abc import ABCMeta, ABC

from six import add_metaclass


"""
first version uses direct inheritance, while limiting the foster parent init
this works, but will still register as a subclass on the parent __bases__

"""

class B(object):
	def __init__(self):
		print( "B init")

	def specificBMethod(self):
		return ("specificB")

	def method(self):
		return "B"
	pass

class DProxyMeta(ABCMeta):

	def __instancecheck__(self, item):
		print("item {}".format(item))
		return True
	pass


@add_metaclass(DProxyMeta)
#class DProxyTest(object):
#class DProxyTest(ABC, dict):
class DProxyTest(ABC, B):

	def __new__(cls, *args, **kwargs):
		print("main new")
		obj = ABC.__new__(cls, *args, **kwargs)
		print("main obj {}".format(obj))
		return obj

	def __init__(self):
		pass


	def method(self):
		return "proxyB"

	def specificDMethod(self):
		return "specificProxyD"

print("------ FIRST VERSION -------")

n = DProxyTest()

isinstance([], DProxyTest)
assert isinstance({}, DProxyTest)
assert isinstance(n, B)
print(n.method())
print(B.__subclasses__())
print("")

"""
second version : overriding __class__
this is so easy, and it works
what's the catch to this?

"""

class DProxyTest(object):

	@property
	def __class__(self):
		return B

	def method(self):
		return "proxyB"

	def specificDMethod(self):
		return "specificProxyD"


print("--------- SECOND VERSION --------")
n = DProxyTest()
b = B()
print(n.method())
print(type(n))
assert isinstance(n, B)
# assert isinstance(b, DProxyTest) # this fails
#print(n.specificBMethod())
print(n.specificDMethod())
print("")



"""
third version
still overriding __class__, but now inheriting from ABC
and using register() to get mutual type equivalence
I'll start with this and see if it blows up
didn't take long - I neglected how restrictive this is
for basic operations within the proxy class - 
self.__class__ no longer gets the parent.
could just do type(self) for those?
"""


class DProxyTest(ABC):

	@property
	def __class__(self):
		return B

	def method(self):
		return "proxyB"

	def specificDMethod(self):
		return "specificProxyD"

DProxyTest.register(B)

print("--------- THIRD VERSION --------")
n = DProxyTest()
b = B()
print(n.method())
print(type(n))
assert isinstance(n, B)
assert isinstance(b, DProxyTest) # this fails
#print(n.specificBMethod())
print(n.specificDMethod())
