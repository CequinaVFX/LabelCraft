#******************************************************
# content: tool to quickly edit node's label and
#          some parameters
#
# version: 2.3.0
# date: September 10 2023
#
# how to: 
# dependencies: nuke
# todos: --//--
#
# license: MIT
# author: Luciano Cequinel [lucianocequinel@gmail.com]
#******************************************************

from os import path
import sys
import re
import nuke

from PySide2 import QtWidgets, QtCore, QtUiTools, QtGui

from PySide2.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QVBoxLayout

#*******************************************************************
# GLOBAL VARIABLES AND LISTS
INFO_NODES = ['BackdropNode', 'StickyNote']

DOT_NODE = ['Dot']

MERGE_NODES = ['Merge2', 'ChannelMerge', 'Keymix']

SWITCH_NODES = ['Dissolve', 'Switch']

FILTER_NODES = ['Blur', 'Defocus', 'Dilate', 'FilterErode', 'Erode', 'Sharpen', 'Soften']

TRACKER_NODES = ['Tracker4', 'Tracker3']

COLORSPACE_NODES = ['Log2Lin', 'OCIOColorSpace', 'Colorspace']

WHICH_EXPRESSIONS = ['$gui', '!$gui', 'value error', 'frame ==', 'frame >', 'frame >=', 'frame <', 'frame <=', 'inrange frame']

INFO_ALIGN = ['left', 'center', 'right']

ICON_SELECTION = ['none', 'Axis', 'Add', 'Bezier', 'Camera',
                  'Color', 'ColorAdd', 'ColorBars', 'ColorCorrect', 'ColorLookup', 
                  'ColorSpace', 'CornerPin', 'Crop','Cube', 'Color', 'CheckerBoard',
                  'Dot', 'EnvironMaps', 'Exposure', 'Expression',
                  'FloodFill', 'Input', 'ImageModeler', 'Keyer', 'MarkerRemoval', 'Merge',
                  'Modify', 'Output', 'Position', 'Primatte', 'Read',
                  'Render', 'RotoPaint', 'Shuffle', 'Sphere',
                  'TimeClip', 'Tracker', 'Viewer', 'Write']

class SmartLabel():
    def __init__(self):

        procedural_path = ([path.dirname(__file__)])
        procedural_TITLE = (path.splitext(path.basename(__file__))[0])
        path_ui = ("/").join([path.dirname(__file__), procedural_TITLE + ".ui"])

        self.SmartLabelUI = QtUiTools.QUiLoader().load(path_ui)

        self.SmartLabelUI.grp_Tracker.setVisible(False)
        self.SmartLabelUI.grp_Merge.setVisible(False)
        self.SmartLabelUI.grp_Info.setVisible(False)
        self.SmartLabelUI.grp_Filter.setVisible(False)
        self.SmartLabelUI.grp_Switch.setVisible(False)
        self.SmartLabelUI.grp_Colorspaces.setVisible(False)
        self.SmartLabelUI.grp_Dot.setVisible(False)

        self.SmartLabelUI.ckx_HideInput.setVisible(False)
        self.SmartLabelUI.ckx_PostageStamp.setVisible(False)
        self.SmartLabelUI.ckx_Bookmark.setVisible(False)


        ######################################################################################
        # SIGNALS
        self.SmartLabelUI.btn_cancel.clicked.connect(self.press_cancel)

        self.SmartLabelUI.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
        self.SmartLabelUI.move(QtGui.QCursor.pos()+QtCore.QPoint(-300,0))
        #self.SmartLabelUI.setDefault()

        # readjust widget window and show it
        self.SmartLabelUI.adjustSize()
        self.SmartLabelUI.show()



    def press_cancel(self):
        self.SmartLabelUI.close()


def run():
    nodes = nuke.selectedNodes()
    if len(nodes) == 1:
        node = nuke.selectedNode()
        global runTool
        runTool = SmartLabel()
    else:
        if len(nodes) > 1:
            nuke.message('Select only one node!')
        else:
            nuke.message('You must select something!')

if __name__ == '__main__':
    global runTool
    try:
        app = QtWidgets.QApplication(sys.argv)
        runTool = SmartLabel()
        app.exec_()
    except:
        run()

