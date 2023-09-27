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

WHICH_EXPRESSIONS = ['$gui', '!$gui', 'value error', 'frame ==', 'frame >',
                     'frame >=', 'frame <', 'frame <=', 'inrange frame']

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
    def __init__(self, node):

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

        #self.SmartLabelUI.edt_NodeLabel.setTabChangesFocus(True)

        self.node = node
        self.SmartLabelUI.grp_Node.setTitle(self.node.name())

        # get current label and fill edt_NodeLabel
        self.currentLabel = self.node['label'].value()
        self.SmartLabelUI.edt_NodeLabel.setText(self.currentLabel)
        self.SmartLabelUI.edt_NodeLabel.selectAll()

        # get current state of hide_input, postage_stamp, bookmark
        if 'hide_input' in self.node.knobs():
            curHide = self.node['hide_input'].value()
            self.SmartLabelUI.ckx_HideInput.setVisible(True)
            self.SmartLabelUI.ckx_HideInput.setChecked(curHide)

        if 'postage_stamp' in self.node.knobs():
            curPostage = self.node['postage_stamp'].value()
            self.SmartLabelUI.ckx_PostageStamp.setVisible(True)
            self.SmartLabelUI.ckx_PostageStamp.setChecked(curPostage)

        if 'bookmark' in self.node.knobs():
            curBookmark = self.node['bookmark'].value()
            self.SmartLabelUI.ckx_Bookmark.setVisible(True)
            self.SmartLabelUI.ckx_Bookmark.setChecked(curBookmark)

        # get current node.Class to send it to specific function
        self.currentClass = 'none'
        if self.node.Class() in TRACKER_NODES:
            self.currentClass = 'tracker'
            self.trackerUI()

        elif self.node.Class() in MERGE_NODES:
            self.currentClass = 'keymix'
            self.mergeUI()

        elif self.node.Class() in INFO_NODES:
            self.currentClass = 'info'
            self.infoUI()

        elif self.node.Class() in SWITCH_NODES:
            self.currentClass = 'switch'
            self.switchUI()

        elif self.node.Class() in COLORSPACE_NODES:
            self.currentClass = 'colorspace'
            self.colorspaceUI()

        elif self.node.Class() in DOT_NODE:
            self.currentClass = 'dot'
            self.dotUI()

        else:
           for knob in self.node.knobs():
               if knob in ('size', 'defocus'):
                       self.currentClass = knob #'filter'
                       self.filterUI()

        ######################################################################################
        # SIGNALS
        self.SmartLabelUI.btn_OK.clicked.connect(self.press_OK)
        self.SmartLabelUI.btn_cancel.clicked.connect(self.press_cancel)
        self.SmartLabelUI.btn_TrackerGetFrame.clicked.connect(self.press_TrackerGetCurrentFrame)
        self.SmartLabelUI.btn_ColorspaceSwap.clicked.connect(self.press_ColorspaceSwap)
        self.SmartLabelUI.spn_FilterSize.valueChanged.connect(self.spin_FilterSize)
        self.SmartLabelUI.sld_FilterSize.valueChanged.connect(self.slide_FilterSize)
        self.SmartLabelUI.spn_FilterSizeB.valueChanged.connect(self.spin_FilterSizeB)
        self.SmartLabelUI.sld_FilterSizeB.valueChanged.connect(self.slide_FilterSizeB)
        self.SmartLabelUI.cbx_InfoAlign.currentTextChanged.connect(self.change_Alignment)
        self.SmartLabelUI.ckx_SwitchExpression.stateChanged.connect(self.change_Switch)
        self.SmartLabelUI.cbx_SwitchExpression.currentTextChanged.connect(self.changeExpression)

        self.SmartLabelUI.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
        self.SmartLabelUI.move(QtGui.QCursor.pos() + QtCore.QPoint(-300,0))
        #self.SmartLabelUI.setDefault()

        self.SmartLabelUI.edt_NodeLabel.setTabChangesFocus(True)
        self.SmartLabelUI.edt_NodeLabel.setFocusPolicy(QtCore.Qt.StrongFocus)      
        self.SmartLabelUI.edt_NodeLabel.setFocus()

        # readjust widget window and show it
        self.SmartLabelUI.adjustSize()
        self.SmartLabelUI.show()


    def get_node(self, node):

        self.node = node
        self.SmartLabelUI.grp_Node.setTitle(self.node.name())

        # get current label and fill edt_NodeLabel
        self.currentLabel = self.node['label'].value()
        self.SmartLabelUI.edt_NodeLabel.setText(self.currentLabel)
        self.SmartLabelUI.edt_NodeLabel.selectAll()

        # get current state of hide_input, postage_stamp, bookmark
        if 'hide_input' in self.node.knobs():
            curHide = self.node['hide_input'].value()
            self.SmartLabelUI.ckx_HideInput.setVisible(True)
            self.SmartLabelUI.ckx_HideInput.setChecked(curHide)

        if 'postage_stamp' in self.node.knobs():
            curPostage = self.node['postage_stamp'].value()
            self.SmartLabelUI.ckx_PostageStamp.setVisible(True)
            self.SmartLabelUI.ckx_PostageStamp.setChecked(curPostage)

        if 'bookmark' in self.node.knobs():
            curBookmark = self.node['bookmark'].value()
            self.SmartLabelUI.ckx_Bookmark.setVisible(True)
            self.SmartLabelUI.ckx_Bookmark.setChecked(curBookmark)

        # get current node.Class to send it to specific function
        self.currentClass = 'none'
        if self.node.Class() in TRACKER_NODES:
            self.currentClass = 'tracker'
            self.trackerUI()

        elif self.node.Class() in MERGE_NODES:
            self.currentClass = 'keymix'
            self.mergeUI()

        elif self.node.Class() in INFO_NODES:
            self.currentClass = 'info'
            self.infoUI()

        elif self.node.Class() in SWITCH_NODES:
            self.currentClass = 'switch'
            self.switchUI()

        elif self.node.Class() in COLORSPACE_NODES:
            self.currentClass = 'colorspace'
            self.colorspaceUI()

        elif self.node.Class() in DOT_NODE:
            self.currentClass = 'dot'
            self.dotUI()

        else:
           for knob in self.node.knobs():
               if knob in ('size', 'defocus'):
                       self.currentClass = knob #'filter'
                       self.filterUI()



        self.SmartLabelUI.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
        self.SmartLabelUI.move(QtGui.QCursor.pos()+QtCore.QPoint(-300,0))

        self.SmartLabelUI.edt_NodeLabel.setTabChangesFocus(True)
        self.SmartLabelUI.edt_NodeLabel.setFocusPolicy(QtCore.Qt.StrongFocus)      
        self.SmartLabelUI.edt_NodeLabel.setFocus()

        signals = self.set_signals()

        # readjust widget window and show it
        self.SmartLabelUI.adjustSize()
        self.SmartLabelUI.show()


    def set_signals(self):
        # SIGNALS
        self.SmartLabelUI.btn_OK.clicked.connect(self.press_OK)
        self.SmartLabelUI.btn_cancel.clicked.connect(self.press_cancel)
        self.SmartLabelUI.btn_TrackerGetFrame.clicked.connect(self.press_TrackerGetCurrentFrame)
        self.SmartLabelUI.btn_ColorspaceSwap.clicked.connect(self.press_ColorspaceSwap)
        self.SmartLabelUI.spn_FilterSize.valueChanged.connect(self.spin_FilterSize)
        self.SmartLabelUI.sld_FilterSize.valueChanged.connect(self.slide_FilterSize)
        self.SmartLabelUI.spn_FilterSizeB.valueChanged.connect(self.spin_FilterSizeB)
        self.SmartLabelUI.sld_FilterSizeB.valueChanged.connect(self.slide_FilterSizeB)
        self.SmartLabelUI.cbx_InfoAlign.currentTextChanged.connect(self.change_Alignment)
        self.SmartLabelUI.ckx_SwitchExpression.stateChanged.connect(self.change_Switch)
        self.SmartLabelUI.cbx_SwitchExpression.currentTextChanged.connect(self.changeExpression)

    def trackerUI(self):
        self.SmartLabelUI.grp_Tracker.setVisible(True)
        self.SmartLabelUI.grp_Tracker.setTitle('change knobs')
        
        knobList = self.node['transform'].values()
        self.SmartLabelUI.cbx_TrackerTransform.addItems(knobList)

        knobValue = str(self.node['transform'].value())
        self.SmartLabelUI.cbx_TrackerTransform.setCurrentText(knobValue)

        reference_frame = int(self.node['reference_frame'].getValue())
        self.SmartLabelUI.spn_TrackerRefFrame.setRange(1, 1000000)
        self.SmartLabelUI.spn_TrackerRefFrame.setValue(reference_frame)

    def mergeUI(self):
        self.SmartLabelUI.grp_Merge.setVisible(True)
        self.SmartLabelUI.grp_Merge.setTitle('change knobs')
        self.SmartLabelUI.cbx_MergeOperation.setEnabled(False)

        if self.currentClass is not 'keymix':
            self.currentClass = 'merge'
            operList = self.node['operation'].values()
            curOper = str(self.node['operation'].value())

            self.SmartLabelUI.cbx_MergeOperation.setEnabled(True)
            self.SmartLabelUI.cbx_MergeOperation.addItems(operList)
            self.SmartLabelUI.cbx_MergeOperation.setCurrentText(curOper)

        boxList = self.node['bbox'].values()
        curBox = str(self.node['bbox'].value())
        self.SmartLabelUI.cbx_MergeBBox.addItems(boxList)
        self.SmartLabelUI.cbx_MergeBBox.setCurrentText(curBox)

    def infoUI(self):
        self.SmartLabelUI.grp_Info.setVisible(True)
        self.SmartLabelUI.grp_Info.setTitle('change knobs')
        
        # set standard values
        align = 'center'
        icon = 'none'

        HTML = re.findall('<(.*?)>', self.currentLabel)

        try:
            align = HTML[0]
        except:
            align = 'center'

        try:
            icon = re.findall('"(.*?).png', HTML[1])[0]
        except:
            icon = 'none'

        self.SmartLabelUI.cbx_InfoAlign.addItems(INFO_ALIGN)
        self.SmartLabelUI.cbx_InfoAlign.setCurrentText(align)
        self.SmartLabelUI.cbx_InfoIcon.addItems(ICON_SELECTION)
        self.SmartLabelUI.cbx_InfoIcon.setCurrentText(icon)
        self.SmartLabelUI.lbl_InfoZOrder.setVisible(False)
        self.SmartLabelUI.spn_InfoZOrder.setVisible(False)

        try:
            self.currentLabel = self.currentLabel.replace('<%s>' % HTML[0], '')
            self.currentLabel = self.currentLabel.replace('<%s>' % HTML[1], '')
        except:
            pass

        self.SmartLabelUI.edt_NodeLabel.setText(self.currentLabel)
        self.SmartLabelUI.edt_NodeLabel.selectAll()

        curFont = int(self.node['note_font_size'].value())
        self.SmartLabelUI.spn_InfoFontSize.setValue(curFont)

        curNoteFont = self.node['note_font'].value()
        print('current font ', curNoteFont)

        try:
            bold = re.findall('Bold', curNoteFont)[0]
        except:
            bold = False

        try:
            italic = re.findall('Italic', curNoteFont)[0]
        except:
            italic = False

        if bold:
            self.SmartLabelUI.ckx_InfoBold.setChecked(True)
        if italic:
            self.SmartLabelUI.ckx_InfoItalic.setChecked(True)

        if 'z_order' in self.node.knobs():
            curOrder = int(self.node['z_order'].value())
            self.SmartLabelUI.lbl_InfoZOrder.setVisible(True)
            self.SmartLabelUI.spn_InfoZOrder.setVisible(True)
            self.SmartLabelUI.spn_InfoZOrder.setRange(-20, 20)
            self.SmartLabelUI.spn_InfoZOrder.setValue(curOrder)

    def filterUI(self):
        self.SmartLabelUI.grp_Filter.setVisible(True)
        self.SmartLabelUI.grp_Filter.setTitle('change knobs')
        self.SmartLabelUI.cbx_FilterChannels.setVisible(False)
        self.SmartLabelUI.lbl_FilterSizeB.setVisible(False)
        self.SmartLabelUI.spn_FilterSizeB.setVisible(False)
        self.SmartLabelUI.sld_FilterSizeB.setVisible(False)

        if 'channels' in self.node.knobs():
            chanList = ['all', 'none', 'rgb', 'rgba', 'alpha'] 
            curChannel = self.node['channels'].value()
            self.SmartLabelUI.cbx_FilterChannels.setVisible(True)
            self.SmartLabelUI.cbx_FilterChannels.addItems(chanList)
            self.SmartLabelUI.cbx_FilterChannels.setCurrentText(curChannel)

        if self.currentClass == 'size':
            curSize = self.node['size'].value()
        if self.currentClass == 'defocus':
            curSize = self.node['defocus'].value()
        
        self.separatedValues = False
        
        try:
            if len(curSize) > 1:
                self.separatedValues = True
                self.SmartLabelUI.lbl_FilterSize.setText('size w')
                self.SmartLabelUI.spn_FilterSize.setRange(-5000, +5000)
                self.SmartLabelUI.sld_FilterSize.setRange(-1000, +1000)
                self.SmartLabelUI.spn_FilterSize.setValue(curSize[0])
                self.SmartLabelUI.sld_FilterSize.setValue(curSize[0])

                self.SmartLabelUI.lbl_FilterSizeB.setVisible(True)
                self.SmartLabelUI.spn_FilterSizeB.setVisible(True)
                self.SmartLabelUI.sld_FilterSizeB.setVisible(True)

                self.SmartLabelUI.spn_FilterSizeB.setRange(-5000, +5000)
                self.SmartLabelUI.sld_FilterSizeB.setRange(-1000, +1000)
                self.SmartLabelUI.spn_FilterSizeB.setValue(curSize[1])
                self.SmartLabelUI.sld_FilterSizeB.setValue(curSize[1])


        except:
            self.SmartLabelUI.spn_FilterSize.setRange(-5000, +5000)
            self.SmartLabelUI.sld_FilterSize.setRange(-1000, +1000)
            self.SmartLabelUI.spn_FilterSize.setValue(curSize)
            self.SmartLabelUI.sld_FilterSize.setValue(curSize)

    def switchUI(self):
        self.SmartLabelUI.grp_Switch.setVisible(True)
        self.SmartLabelUI.grp_Switch.setTitle('change knobs')
        self.SmartLabelUI.cbx_SwitchExpression.setVisible(False)
        self.SmartLabelUI.cbx_SwitchExpression.addItems(WHICH_EXPRESSIONS)

        curValueA = nuke.frame()
        curValueB = nuke.frame() + 10

        self.addKnobs = True
        if 'expression' in self.node.knobs():
            checkExpression = self.node['check_expression'].value()
            self.SmartLabelUI.ckx_SwitchExpression.setChecked(checkExpression)
            self.addKnobs = False

            curExpression = self.node['expression'].value()
            curValueA = self.node['valueA'].value()
            curValueB = self.node['valueB'].value()

            self.SmartLabelUI.cbx_SwitchExpression.setCurrentText(curExpression)

        self.SmartLabelUI.spn_SwitchValueA.setVisible(False)
        self.SmartLabelUI.spn_SwitchValueA.setRange(1, 1000000)
        self.SmartLabelUI.spn_SwitchValueA.setValue(curValueA)
        self.SmartLabelUI.spn_SwitchValueB.setVisible(False)
        self.SmartLabelUI.spn_SwitchValueB.setRange(1, 1000000)
        self.SmartLabelUI.spn_SwitchValueB.setValue(curValueB)

        if self.SmartLabelUI.ckx_SwitchExpression.checkState():
            self.SmartLabelUI.edt_SwitchWhich.setEnabled(False)
            self.SmartLabelUI.cbx_SwitchExpression.setEnabled(True)
            self.SmartLabelUI.spn_SwitchValueA.setEnabled(True)
            self.SmartLabelUI.spn_SwitchValueA.setVisible(True)
            if curExpression.startswith('inrange'):
                self.SmartLabelUI.spn_SwitchValueB.setEnabled(True)
                self.SmartLabelUI.spn_SwitchValueB.setVisible(True)
        else:
            self.SmartLabelUI.edt_SwitchWhich.setEnabled(True)
            self.SmartLabelUI.cbx_SwitchExpression.setEnabled(False)

    def colorspaceUI(self):
        self.SmartLabelUI.grp_Colorspaces.setVisible(True)
        self.SmartLabelUI.grp_Colorspaces.setTitle('change knobs')

        self.SmartLabelUI.cbx_ColorValueA.setVisible(False)
        self.SmartLabelUI.cbx_ColorValueB.setVisible(False)
        self.SmartLabelUI.btn_ColorspaceSwap.setVisible(False)

        if self.node.Class() == 'Log2Lin':
            self.currentClass = 'log'

            curOper = str(self.node['operation'].value())
            operList = self.node['operation'].values()

            self.SmartLabelUI.cbx_ColorValueA.setVisible(True)
            self.SmartLabelUI.cbx_ColorValueA.addItems(operList)
            self.SmartLabelUI.cbx_ColorValueA.setCurrentText(curOper)

        else:
            if self.node.Class() == 'OCIOColorSpace':
                self.currentClass = 'OCIOColorSpace'
                curOperA = str(self.node['in_colorspace'].value())
                curOperB = str(self.node['out_colorspace'].value())
                operList = self.node['in_colorspace'].values()

            if self.node.Class() == 'Colorspace':
                curOperA = int(self.node['colorspace_in'].getValue())
                curOperB = int(self.node['colorspace_out'].getValue())
                operList = self.node['colorspace_in'].values()

            editList = []
            for item in operList:
                if re.findall('\\t', item):
                    g = item.split('\t')[1]
                    editList.append(g)
                else:
                    editList.append(item)

            self.SmartLabelUI.cbx_ColorValueA.setVisible(True)
            self.SmartLabelUI.cbx_ColorValueB.setVisible(True)
            self.SmartLabelUI.btn_ColorspaceSwap.setVisible(True)

            self.SmartLabelUI.cbx_ColorValueA.addItems(editList)
            self.SmartLabelUI.cbx_ColorValueA.setCurrentIndex(curOperA)
            self.SmartLabelUI.cbx_ColorValueB.addItems(editList)
            self.SmartLabelUI.cbx_ColorValueB.setCurrentIndex(curOperB)

    def dotUI(self):
        self.SmartLabelUI.grp_Dot.setVisible(True)
        self.SmartLabelUI.grp_Dot.setTitle('change knobs')

        curFont = int(self.node['note_font_size'].value())
        self.SmartLabelUI.spn_DotFontSize.setValue(curFont)

        curNoteFont = self.node['note_font'].value()
        bold = re.findall('Bold', curNoteFont)
        italic = re.findall('Italic', curNoteFont)

        if bold:
            self.SmartLabelUI.ckx_DotBold.setChecked(True)
        if italic:
            self.SmartLabelUI.ckx_DotItalic.setChecked(True)

    ###############################################################################
    # USER INTERACTION EVENTS
    def press_TrackerGetCurrentFrame(self):
        newFrame = nuke.frame()
        self.SmartLabelUI.spn_TrackerRefFrame.setValue(newFrame)

    def spin_FilterSize(self):
        newValue = float(self.SmartLabelUI.spn_FilterSize.value())
        self.SmartLabelUI.sld_FilterSize.setValue(newValue)

    def slide_FilterSize(self):
        newValue = float(self.SmartLabelUI.sld_FilterSize.value())
        self.SmartLabelUI.spn_FilterSize.setValue(newValue)

    def spin_FilterSizeB(self):
        newValue = float(self.SmartLabelUI.spn_FilterSizeB.value())
        self.SmartLabelUI.sld_FilterSizeB.setValue(newValue)

    def slide_FilterSizeB(self):
        newValue = float(self.SmartLabelUI.sld_FilterSizeB.value())
        self.SmartLabelUI.spn_FilterSizeB.setValue(newValue)

    def press_ColorspaceSwap(self):
        valA = str(self.SmartLabelUI.cbx_ColorValueA.currentText())
        valB = str(self.SmartLabelUI.cbx_ColorValueB.currentText())
        self.SmartLabelUI.cbx_ColorValueA.setCurrentText(valB)
        self.SmartLabelUI.cbx_ColorValueB.setCurrentText(valA)

    def change_Alignment(self):
        newAlign = str(self.SmartLabelUI.cbx_InfoAlign.currentText())

        if newAlign == 'center':
            self.SmartLabelUI.edt_NodeLabel.setAlignment(QtCore.Qt.AlignCenter)
        elif newAlign == 'left':
            self.SmartLabelUI.edt_NodeLabel.setAlignment(QtCore.Qt.AlignLeft)
        if newAlign == 'right':
            self.SmartLabelUI.edt_NodeLabel.setAlignment(QtCore.Qt.AlignRight)

    def change_Switch(self):

        if self.SmartLabelUI.ckx_SwitchExpression.checkState() or self.checkExpressions:
            self.SmartLabelUI.lbl_SwitchWhich.setEnabled(False)
            self.SmartLabelUI.edt_SwitchWhich.setEnabled(False)
            self.SmartLabelUI.cbx_SwitchExpression.setEnabled(True)
            self.SmartLabelUI.cbx_SwitchExpression.setVisible(True)

            newExpression = str(self.SmartLabelUI.cbx_SwitchExpression.currentText())

            if newExpression.startswith('frame'):
                self.SmartLabelUI.spn_SwitchValueA.setVisible(True)
                self.SmartLabelUI.spn_SwitchValueB.setVisible(False)
            elif newExpression.startswith('inrange'):
                self.SmartLabelUI.spn_SwitchValueA.setVisible(True)
                self.SmartLabelUI.spn_SwitchValueB.setVisible(True)
            else:
                self.SmartLabelUI.spn_SwitchValueA.setVisible(False)
                self.SmartLabelUI.spn_SwitchValueB.setVisible(False)

        else:
            self.SmartLabelUI.lbl_SwitchWhich.setEnabled(True)
            self.SmartLabelUI.edt_SwitchWhich.setEnabled(True)
            self.SmartLabelUI.cbx_SwitchExpression.setEnabled(False)
            self.SmartLabelUI.cbx_SwitchExpression.setVisible(False)
            self.SmartLabelUI.spn_SwitchValueA.setEnabled(False)
            self.SmartLabelUI.spn_SwitchValueA.setVisible(False)
            self.SmartLabelUI.spn_SwitchValueB.setEnabled(False)
            self.SmartLabelUI.spn_SwitchValueB.setVisible(False)

    def changeExpression(self):
        newExpression = str(self.SmartLabelUI.cbx_SwitchExpression.currentText())

        if newExpression.startswith('frame'):
            self.SmartLabelUI.spn_SwitchValueA.setVisible(True)
            self.SmartLabelUI.spn_SwitchValueB.setVisible(False)
        elif newExpression.startswith('inrange'):
            self.SmartLabelUI.spn_SwitchValueA.setVisible(True)
            self.SmartLabelUI.spn_SwitchValueB.setVisible(True)
        else:
            self.SmartLabelUI.spn_SwitchValueA.setVisible(False)
            self.SmartLabelUI.spn_SwitchValueB.setVisible(False)

    def press_OK(self):
        #newLabel = self.SmartLabelUI.edt_NodeLabel.text()
        newLabel = self.SmartLabelUI.edt_NodeLabel.toPlainText()

        # set options
        if self.currentClass not in ('dot', 'info'):        
            newHide = self.SmartLabelUI.ckx_HideInput.checkState()
            curHide = self.node['hide_input'].setValue(newHide)

            newPostage = self.SmartLabelUI.ckx_PostageStamp.checkState()
            curPostage = self.node['postage_stamp'].setValue(newPostage)
            
            newBookmark = self.SmartLabelUI.ckx_Bookmark.checkState()
            curBookmark = self.node['bookmark'].setValue(newBookmark)

        # set knob values for each class
        if self.currentClass == 'tracker':
            newTransform = str(self.SmartLabelUI.cbx_TrackerTransform.currentText())
            self.node['transform'].setValue(newTransform)

            newRef = int(self.SmartLabelUI.spn_TrackerRefFrame.value())
            self.node['reference_frame'].setValue(newRef)

        elif self.currentClass == 'merge':
            newOper = str(self.SmartLabelUI.cbx_MergeOperation.currentText())
            self.node['operation'].setValue(newOper)

            newBBox = str(self.SmartLabelUI.cbx_MergeBBox.currentText())
            self.node['bbox'].setValue(newBBox)

        elif self.currentClass == 'keymix':
            newBBox = str(self.SmartLabelUI.cbx_MergeBBox.currentText())
            self.node['bbox'].setValue(newBBox)

        elif self.currentClass in ('size', 'defocus'):
            newChannel = str(self.SmartLabelUI.cbx_FilterChannels.currentText())
            self.node['channels'].setValue(newChannel)

            newSize = [self.SmartLabelUI.spn_FilterSize.value()]
            if 'size' in self.node.knobs():
                if self.separatedValues:
                    newSize.append(self.SmartLabelUI.spn_FilterSizeB.value())
                    self.node['size'].setValue(newSize)
                else:
                    self.node['size'].setValue(newSize[0])

            elif 'defocus' in self.node.knobs():
                if self.separatedValues:
                    newSize.append(self.SmartLabelUI.spn_FilterSizeB.value())
                    self.node['defocus'].setValue(newSize)
                else:
                    self.node['defocus'].setValue(newSize[0])

        elif self.currentClass == 'log':
            newOper = str(self.SmartLabelUI.cbx_ColorValueA.currentText())
            self.node['operation'].setValue(newOper)

        elif self.currentClass == 'OCIOColorSpace':
            newOper = str(self.SmartLabelUI.cbx_ColorValueA.currentText())
            self.node['in_colorspace'].setValue(newOper)

            newOper = str(self.SmartLabelUI.cbx_ColorValueB.currentText())
            self.node['out_colorspace'].setValue(newOper)

        elif self.currentClass == 'colorspace':
            newOper = (self.SmartLabelUI.cbx_ColorValueA.currentIndex())
            self.node['colorspace_in'].setValue(newOper)

            newOper = (self.SmartLabelUI.cbx_ColorValueB.currentIndex())
            self.node['colorspace_out'].setValue(newOper)

        elif self.currentClass == 'dot':
            newFontSize = int(self.SmartLabelUI.spn_DotFontSize.value())
            newBold = self.SmartLabelUI.ckx_DotBold.checkState()
            newItalic = self.SmartLabelUI.ckx_DotItalic.checkState()
            
            self.node['note_font_size'].setValue(newFontSize)
            self.node['note_font'].setValue('Verdana')
            if newBold:
                self.node['note_font'].setValue('Verdana Bold')
            if newItalic:
                self.node['note_font'].setValue('Verdana Italic')
            if newBold and newItalic:
                self.node['note_font'].setValue('Verdana Bold Italic')

        elif self.currentClass == 'info':
            newAlign = str(self.SmartLabelUI.cbx_InfoAlign.currentText())
            newIcon = str(self.SmartLabelUI.cbx_InfoIcon.currentText())

            if newIcon == 'none':
                newLabel = '<{}>{}'.format(newAlign, newLabel)
            else:
                newLabel = '<{}><img src = "{}.png">{}'.format(newAlign, newIcon, newLabel)

            newFontSize = int(self.SmartLabelUI.spn_InfoFontSize.value())
            newBold = self.SmartLabelUI.ckx_InfoBold.checkState()
            newItalic = self.SmartLabelUI.ckx_InfoItalic.checkState()

            self.node['note_font_size'].setValue(newFontSize)
            self.node['note_font'].setValue('Verdana')
            if newBold:
                self.node['note_font'].setValue('Verdana Bold')
            if newItalic:
                self.node['note_font'].setValue('Verdana Italic')
            if newBold and newItalic:
                self.node['note_font'].setValue('Verdana Bold Italic')

        elif self.currentClass == 'switch':
            if self.SmartLabelUI.ckx_SwitchExpression.checkState():
                if self.addKnobs:
                    self.node.addKnob(nuke.Text_Knob('txt', '', 'smartLabel expressions control'))
                    checkExp = nuke.Boolean_Knob('check_expression', '')
                    checkExp.setVisible(False)
                    self.node.addKnob(checkExp)

                    expKnob = nuke.String_Knob('expression', '')
                    expKnob.setVisible(False)
                    self.node.addKnob(expKnob)

                    valAKnob = nuke.Int_Knob('valueA', 'value A')
                    self.node.addKnob(valAKnob)

                    valBKnob = nuke.Int_Knob('valueB', 'value B')
                    valBKnob.clearFlag(nuke.STARTLINE)
                    self.node.addKnob(valBKnob)

                expression = str(self.SmartLabelUI.cbx_SwitchExpression.currentText())
                self.node['expression'].setValue(expression)

                if expression == 'value error':
                    expression = '[value error]'
                    self.node['valueA'].setVisible(False)
                    self.node['valueB'].setVisible(False)

                elif expression.startswith('frame'):
                    valueA = (self.SmartLabelUI.spn_SwitchValueA.value())
                    self.node['valueA'].setValue(valueA)
                    self.node['valueB'].setVisible(False)
                    expression = '{} valueA'.format(expression, valueA)
                
                elif expression.startswith('inrange'):
                    valueA = self.SmartLabelUI.spn_SwitchValueA.value()
                    valueB = self.SmartLabelUI.spn_SwitchValueB.value()
                    self.node['valueA'].setValue(valueA)
                    self.node['valueB'].setValue(valueB)
                    self.node['valueB'].setVisible(True)

                    expression = 'inrange(frame, valueA, valueB)'

                else:
                    self.node['valueA'].setVisible(False)
                    self.node['valueB'].setVisible(False)

                self.node['check_expression'].setValue(True)
                self.node['which'].setExpression(expression)

            else:
                expression = str(self.SmartLabelUI.edt_SwitchWhich.text())
                self.node['which'].clearAnimated()
                try:
                    self.node['check_expression'].setValue(False)
                except:
                    pass

        if self.currentClass not in INFO_NODES:
            # remove special characters from label
            newLabel = newLabel.encode('ascii', errors='ignore').decode('utf-8')

        # set label
        self.node['label'].setValue(newLabel)

        self.SmartLabelUI.close()

    def press_cancel(self):
        self.SmartLabelUI.close()


def run():
    nodes = nuke.selectedNodes()
    if len(nodes) == 1:
        node = nuke.selectedNode()
        global runTool
        runTool = SmartLabel(node)
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