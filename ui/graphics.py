
""" for any graphics items used in tree ui
maybe we actually just turn these into
their own model view widgets?
or maybe we focus our time on more productive things,
nobody actually needs this """

from PySide2 import QtCore, QtWidgets, QtGui


class ListDragItem(QtWidgets.QGraphicsRectItem):
	""" rectangle lying over single cell of list"""

