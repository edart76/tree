

""" demo for an interesting problem in reference vs value """

class BoolWrapper(object):
	def __init__(self, value):
		self.value = value
	def __repr__(self):
		return self.value
	def __str__(self):
		return str(self.value)

class MainClass(object):
	def __init__(self):
		self.data = BoolWrapper(True)

obj = MainClass()
print("base value", obj.data)

varA = obj.data
print("varA ", varA)

varC = varA # varC set to same as varA

obj.data.value = False

varB = obj.data
print("varA ", varA)
print("varB ", varB)
print("varC ", varC)


