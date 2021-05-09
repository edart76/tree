

"""always had to test out decorator syntax when working with objects
"""

import functools

class DecoClass(object):

	def deco(self, *args, **kwargs): # receives function without call,
		# receives decorator args with call
		print("decoClass deco", args, kwargs)
		def fnWrapper(*wrapArgs, **wrapKwargs):
			# arg 1 is method object
			print("decoClass deco fnWrapper", wrapArgs, wrapKwargs)
			def fnCallWrapper(*wrapCallArgs, **wrapCallKwargs):
				# arg 1 is method class object
				print("decoClass deco fnCallWrapper",
				      wrapCallArgs, wrapCallKwargs)
			return fnCallWrapper

		return fnWrapper


class MainClass(object):

	decoCls = DecoClass()

	@decoCls.deco("eyey") # with brackets, counts as proper call
	# sends empty args to outer layer
	def mainTestFn(self, *testArgs, **testKwargs):
		print("mainTestFn", testArgs, testKwargs)


m = MainClass()

m.mainTestFn(5858)


