
import os, sys
from PySide2 import QtCore, QtWidgets, QtGui


from tree.ui import RESOURCE_DIR
#ICON_PATH = CURRENT_PATH + "/tesserae/ui2/"

ICON_PATH = RESOURCE_DIR
ICON_PATH = ICON_PATH.replace("\\", "/")

# square icons
#squareCentre = QtGui.QPixmap() # QPixmap crashes for some reason


doIcons = False

squarePath = ICON_PATH + "square_centre.png"
downPath = ICON_PATH + "square_down.png"

styleSheet = """
QTreeView::branch::open::has-children {
    image: url('@square_down@');
}
QTreeView::branch::closed::has-children {
    image: url('@square_centre@');
}
QTreeView::branch {
	background-color: rgb(100, 100, 128);
	}
"""

subs = {"@square_centre@": squarePath,
        "@square_down@": downPath}

for k, v in subs.items():
	styleSheet = styleSheet.replace(k, v)

squareDown = squareCentre = squareSides = None

if doIcons:



	#squareDown = QtGui.QPixmap(downPath)
	#squareDown = QtGui.QImage(downPath)
	#print(squarePath)
	squareDown = QtGui.QIcon(downPath)
	#squareCentre = QtGui.QImage(squarePath)
	squareCentre = QtGui.QIcon(squarePath)
	squareSides = {}

	print(2)

	for i, key in enumerate(["down", "left", "up", "right"]):
		tf = QtGui.QTransform()
		tf.rotate(90 * i)
		squareSides[key] = squareDown.transformed(tf)

	#icon-size: 32px 32px;
	print(3)



