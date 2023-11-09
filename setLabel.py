from os import path
import sys
import re
import nuke
from PySide2 import QtWidgets, QtCore, QtUiTools, QtGui
from PySide2.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QVBoxLayout


class SetLabel():
    def __init__(self):
        
        procedural_path = ([path.dirname(__file__)])
        procedural_TITLE = (path.splitext(path.basename(__file__))[0])
        path_ui = ("/").join([path.dirname(__file__), 'SmartLabel' + ".ui"])

        path_ui = 'B:/_CQNTools_/smartLabel/SmartLabel.ui'
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

        self.SmartLabelUI.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
        self.SmartLabelUI.move(QtGui.QCursor.pos() + QtCore.QPoint(-300,0))
        #self.SmartLabelUI.setDefault()

        self.SmartLabelUI.adjustSize()


    def get_nodes(self):
        print('getting nodes')
        nodes = nuke.selectedNodes()
        if len(nodes) == 1:
            self.set_label(nodes[0])

    def set_label(self, node):
        print(node.name())
        self.SmartLabelUI.grp_Node.setTitle('My Title')
        ui = self.SmartLabelUI.show()
        print(ui)




def run():
    node = nuke.selectedNode()
    global runTool
    runTool = SetLabel().get_nodes()

    '''
    nodes = nuke.selectedNodes()
    if len(nodes) == 1:
        node = nuke.selectedNode()
        global runTool
        runTool = SetLabel().set_label(node)
    else:
        if len(nodes) > 1:
            nuke.message('Select only one node!')
        else:
            nuke.message('You must select something!')
    '''
if __name__ == '__main__':
    global runTool
    try:
        app = QtWidgets.QApplication(sys.argv)
        runTool = SetLabel()
        app.exec_()
    except:
        run()