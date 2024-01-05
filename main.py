__title__ = 'LabelCraft'
__author__ = 'Luciano Cequinel'
__contact__ = 'lucianocequinel@gmail.com'
__version__ = '1.0.4'
__release_date__ = 'January, 10 2024'
__license__ = 'MIT'


import nuke
import os.path
import re
from PySide2 import QtUiTools, QtCore, QtGui
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QFontComboBox

ICON_SELECTION = ['none', 'Axis', 'Add', 'Bezier', 'Camera',
                  'Color', 'ColorAdd', 'ColorBars', 'ColorCorrect', 'ColorLookup',
                  'ColorSpace', 'CornerPin', 'Crop', 'Cube', 'Color', 'CheckerBoard',
                  'Dot', 'EnvironMaps', 'Exposure', 'Expression', 'FloodFill',
                  'Input', 'ImageModeler', 'Keyer', 'Light', 'MarkerRemoval',
                  'Merge', 'Modify', 'Output', 'Position', 'Primatte', 'Read',
                  'Render', 'RotoPaint', 'Shuffle', 'Sphere',
                  'TimeClip', 'Tracker', 'Viewer', 'Write']


class LabelCraft:
    def __init__(self):
        """
            Start UI
        """
        # dir_path = 'B:/_CQNTools_/LabelCraft'  # os.path.dirname(__file__)
        dir_path = os.path.dirname(__file__)
        path_ui = '/'.join([dir_path, __title__ + '.ui'])

        self.LabelCraftUI = QtUiTools.QUiLoader().load(path_ui)
        self.LabelCraftUI.setWindowTitle(__title__)

        # create Class attributes
        self.node = None
        self.current_label = None
        self.current_node_class = 'none'
        self.align_state = 'none'
        self.icon_state = 'none'

        # Set all groups to invisible and show the node.Class() related
        self.LabelCraftUI.grp_Read.setVisible(False)
        self.LabelCraftUI.grp_Roto.setVisible(False)
        self.LabelCraftUI.grp_Tracker.setVisible(False)
        self.LabelCraftUI.grp_Merge.setVisible(False)
        self.LabelCraftUI.grp_Info.setVisible(False)
        self.LabelCraftUI.grp_Filter.setVisible(False)
        self.LabelCraftUI.grp_Switch.setVisible(False)
        self.LabelCraftUI.grp_Colorspaces.setVisible(False)

        self.LabelCraftUI.btn_OK.setVisible(False)
        self.LabelCraftUI.btn_Discard.setVisible(False)

    # Label Knob
    def label_knob(self, node):
        if self.current_node_class in ('backdropnode', 'stickynote'):
            self.current_label = node['label'].value()
            self.align_state, self.icon_state = self.get_html()
        else:
            self.current_label = node['label'].value()

        self.LabelCraftUI.edt_NodeLabel.setText(self.current_label)
        self.LabelCraftUI.edt_NodeLabel.selectAll()
        self.LabelCraftUI.edt_NodeLabel.setTabChangesFocus(True)

        self.LabelCraftUI.edt_NodeLabel.setFocusPolicy(Qt.StrongFocus)
        self.LabelCraftUI.edt_NodeLabel.setFocus()

        # if self.current_node_class == 'text':
        #     self.LabelCraftUI.edt_NodeLabel.textChanged.connect(self.change_message)
        # else:
        self.LabelCraftUI.edt_NodeLabel.textChanged.connect(self.change_label)
        self.LabelCraftUI.btn_NodeColor.clicked.connect(self.change_node_color)
        # return current_label

    def change_label(self):
        new_label = self.LabelCraftUI.edt_NodeLabel.toPlainText()

        if self.current_node_class in ('backdropnode', 'stickynote', 'dot'):
            encode_label = new_label.encode('ascii', errors='ignore').decode('utf-8')
            label_dict = {'label': encode_label,
                          'icon': '',
                          'bold': '',
                          'italic': '',
                          'align': ''}

            new_align = '<{}>'.format(str(self.LabelCraftUI.cbx_InfoAlign.currentText()))
            new_icon = str(self.LabelCraftUI.cbx_InfoIcon.currentText())

            label_dict['align'] = new_align

            if new_icon == 'none':
                label_dict['icon'] = ''
            else:
                label_dict['icon'] = '<img src = "{}.png">'.format(new_icon)

            if self.LabelCraftUI.ckx_InfoBold.checkState():
                label_dict['bold'] = '<b>'

            if self.LabelCraftUI.ckx_InfoItalic.checkState():
                label_dict['italic'] = '<i>'

            if self.current_node_class == 'dot':
                info_label = '{bold}{italic}{label}'.format(**label_dict)
            else:
                info_label = '{align}{bold}{italic}{icon}{label}'.format(**label_dict)

            self.node['label'].setValue(info_label)

        else:
            self.node['label'].setValue(new_label)

    def change_node_color(self):
        old_color = self.node['tile_color'].value()
        new_color = nuke.getColor(old_color)
        self.node['tile_color'].setValue(new_color)

    # Common Knobs (HideInput, PostageStamp, Bookmark)
    def common_knobs(self, node):
        self.LabelCraftUI.ckx_HideInput.setVisible(False)
        self.LabelCraftUI.ckx_PostageStamp.setVisible(False)
        self.LabelCraftUI.ckx_Bookmark.setVisible(False)

        if 'hide_input' in node.knobs():
            hide_status = node['hide_input'].value()
            self.LabelCraftUI.ckx_HideInput.setVisible(True)
            self.LabelCraftUI.ckx_HideInput.setChecked(hide_status)

        if 'postage_stamp' in node.knobs():
            postage_status = node['postage_stamp'].value()
            self.LabelCraftUI.ckx_PostageStamp.setVisible(True)
            self.LabelCraftUI.ckx_PostageStamp.setChecked(postage_status)

        if 'bookmark' in node.knobs():
            bookmark_status = node['bookmark'].value()
            self.LabelCraftUI.ckx_Bookmark.setVisible(True)
            self.LabelCraftUI.ckx_Bookmark.setChecked(bookmark_status)

        self.LabelCraftUI.ckx_HideInput.stateChanged.connect(self.change_hide_input)
        self.LabelCraftUI.ckx_PostageStamp.stateChanged.connect(self.change_postage)
        self.LabelCraftUI.ckx_Bookmark.stateChanged.connect(self.change_bookmark)

    def change_hide_input(self):
        self.node['hide_input'].setValue(self.LabelCraftUI.ckx_HideInput.checkState())

    def change_postage(self):
        self.node['postage_stamp'].setValue(self.LabelCraftUI.ckx_PostageStamp.checkState())

    def change_bookmark(self):
        self.node['bookmark'].setValue(self.LabelCraftUI.ckx_Bookmark.checkState())

    def get_layers(self):
        # standard_layers = ['rgb', 'rgba', 'alpha']

        # extended_layer_list = []
        # for layer in nuke.layers(self.node):
        #     # if layer not in standard_layers:
        #     extended_layer_list.append(layer)
        #
        # if sorted(standard_layers) == sorted(extended_layer_list):
        #     return None  # sorted(standard_layers)
        # else:
        #     return sorted(extended_layer_list)
        node_layers = nuke.layers(self.node)
        node_layers.append('none')
        return sorted(node_layers)

    # Read Class functions
    def read_class(self):
        self.LabelCraftUI.grp_Read.setVisible(True)

        colorspace_options = self.node['colorspace'].values()
        colorspace_state = self.node['colorspace'].value()
        self.LabelCraftUI.cbx_Colorspace.addItems(colorspace_options)
        self.LabelCraftUI.cbx_Colorspace.setCurrentText(colorspace_state)

        self.LabelCraftUI.lbl_ReadChannels.setVisible(False)
        self.LabelCraftUI.cbx_Channels.setVisible(False)
        self.LabelCraftUI.btn_Shuffle.setVisible(False)

        valid_layers = self.get_layers()
        self.LabelCraftUI.lbl_ReadChannels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.setVisible(True)
        self.LabelCraftUI.btn_Shuffle.setVisible(True)
        self.LabelCraftUI.cbx_Channels.addItems(valid_layers)
        self.LabelCraftUI.btn_Shuffle.clicked.connect(self.shuffle_layer)

        self.LabelCraftUI.cbx_Colorspace.currentTextChanged.connect(self.change_read_colorspace)

    def shuffle_class(self):
        self.LabelCraftUI.grp_Read.setVisible(True)
        self.LabelCraftUI.lbl_ReadColorspace.setVisible(False)
        self.LabelCraftUI.cbx_Colorspace.setVisible(False)

        self.LabelCraftUI.btn_Shuffle.setVisible(True)

        valid_layers = self.get_layers()
        # if valid_layers:
        self.LabelCraftUI.lbl_ReadChannels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.setVisible(True)
        # self.LabelCraftUI.btn_Shuffle.setVisible(True)
        self.LabelCraftUI.cbx_Channels.addItems(valid_layers)
        self.LabelCraftUI.btn_Shuffle.clicked.connect(self.shuffle_layer)

        self.LabelCraftUI.cbx_Colorspace.currentTextChanged.connect(self.change_shuffle_channel)

    def change_read_colorspace(self):
        self.node['colorspace'].setValue(str(self.LabelCraftUI.cbx_Colorspace.currentText()))

    def change_shuffle_channel(self):
        if self.current_node_class == 'shuffle':
            self.node['in'].setValue(str(self.LabelCraftUI.cbx_Channels.currentText()))

        elif self.current_node_class == 'shuffle2':
            self.node['in1'].setValue(str(self.LabelCraftUI.cbx_Channels.currentText()))

    def shuffle_layer(self):
        chosen_layer = str(self.LabelCraftUI.cbx_Channels.currentText())

        if chosen_layer != 'none':
            # node_outputs = nuke.dependentNodes(nuke.INPUTS | nuke.HIDDEN_INPUTS | nuke.EXPRESSIONS, [self.node])

            shuffle_node = nuke.nodes.Shuffle(name="Shuffle_" + chosen_layer)
            shuffle_node.knob("in").setValue(chosen_layer)
            # shuffle_node["hide_input"].setValue(True)
            shuffle_node["postage_stamp"].setValue(True)

            shuffle_node.setInput(0, self.node)

    # Tracker Class functions
    def tracker_class(self):
        # set group to visible and edit the group's name
        self.LabelCraftUI.grp_Tracker.setVisible(True)
        self.LabelCraftUI.grp_Tracker.setTitle('Tracker knobs')

        transform_options = self.node['transform'].values()
        self.LabelCraftUI.cbx_TrackerTransform.addItems(transform_options)

        transform_state = str(self.node['transform'].value())
        self.LabelCraftUI.cbx_TrackerTransform.setCurrentText(transform_state)

        reference_frame = int(self.node['reference_frame'].getValue())
        self.LabelCraftUI.spn_TrackerRefFrame.setRange(1, 1000000)
        self.LabelCraftUI.spn_TrackerRefFrame.setValue(reference_frame)

        self.get_tracks_names()
        # add signal
        self.LabelCraftUI.cbx_TrackerTransform.currentTextChanged.connect(self.change_transform)
        self.LabelCraftUI.spn_TrackerRefFrame.valueChanged.connect(self.change_reference)
        self.LabelCraftUI.btn_TrackerGetFrame.clicked.connect(self.press_get_current_frame)

    def get_tracks_names(self):
        n = self.node["tracks"].toScript()
        rows = n.split("\n")[34:]

        trackers = []
        for i in rows:
            try:
                track_name = i.split("}")[1].split("{")[0][2:-2]
                if track_name != "":
                    trackers.append(track_name)
                    print(track_name)
            except:
                continue

        # return trackers

    def change_reference(self):
        self.node['reference_frame'].setValue(self.LabelCraftUI.spn_TrackerRefFrame.value())

    def change_transform(self):
        self.node['transform'].setValue(str(self.LabelCraftUI.cbx_TrackerTransform.currentText()))

    def press_get_current_frame(self):
        self.LabelCraftUI.spn_TrackerRefFrame.setValue(nuke.frame())
        self.node['reference_frame'].setValue(nuke.frame())

    # Merge Class functions
    def merge_class(self):
        # set group to visible and edit the group's name
        self.LabelCraftUI.grp_Merge.setVisible(True)
        self.LabelCraftUI.grp_Merge.setTitle('{} knobs'.format(self.node.Class()))

        # assume node class as Keymix to start and avoid operation error
        self.LabelCraftUI.cbx_MergeOperation.setEnabled(False)
        self.LabelCraftUI.cbx_MergeOperation.addItem('no operation for Keymix')
        self.LabelCraftUI.cbx_MergeOperation.setCurrentText('no operation for Keymix')

        # only enable operation knob when exists
        if 'operation' in self.node.knobs():
            self.current_node_class = 'merge'
            self.LabelCraftUI.cbx_MergeOperation.setEnabled(True)

            operation_options = self.node['operation'].values()
            self.LabelCraftUI.cbx_MergeOperation.addItems(operation_options)

            operation_state = str(self.node['operation'].value())
            self.LabelCraftUI.cbx_MergeOperation.setCurrentText(operation_state)

        # bbox knob
        bbox_options = self.node['bbox'].values()
        self.LabelCraftUI.cbx_MergeBBox.addItems(bbox_options)

        bbox_state = str(self.node['bbox'].value())
        self.LabelCraftUI.cbx_MergeBBox.setCurrentText(bbox_state)

        # mix knob
        mix_state = self.node['mix'].value()

        self.LabelCraftUI.spn_Mix.setRange(0, 1)
        self.LabelCraftUI.spn_Mix.setValue(mix_state)

        self.LabelCraftUI.sld_Mix.setValue(int(mix_state * 100))
        self.LabelCraftUI.sld_Mix.setRange(0, 100)

        # Signals
        self.LabelCraftUI.cbx_MergeOperation.currentTextChanged.connect(self.change_operation)
        self.LabelCraftUI.cbx_MergeBBox.currentTextChanged.connect(self.change_bbox)
        self.LabelCraftUI.spn_Mix.valueChanged.connect(self.change_spin_mix)
        self.LabelCraftUI.sld_Mix.valueChanged.connect(self.change_slider_mix)

    def change_operation(self):
        new_operation = str(self.LabelCraftUI.cbx_MergeOperation.currentText())
        self.node['operation'].setValue(new_operation)

    def change_bbox(self):
        new_bbox = str(self.LabelCraftUI.cbx_MergeBBox.currentText())
        self.node['bbox'].setValue(new_bbox)

    def change_spin_mix(self):
        new_mix = float(self.LabelCraftUI.spn_Mix.value())
        self.LabelCraftUI.sld_Mix.setValue(int(new_mix * 100))

        self.node['mix'].setValue(new_mix)

    def change_slider_mix(self):
        new_mix = (float(self.LabelCraftUI.sld_Mix.value()) / 100)
        self.LabelCraftUI.spn_Mix.setValue(new_mix)

        self.node['mix'].setValue(new_mix)

    # Roto/ RotoPaint Class functions
    def roto_class(self):
        self.LabelCraftUI.grp_Roto.setVisible(True)
        self.LabelCraftUI.grp_Roto.setTitle(self.node.Class())

        valid_layers = self.get_layers()

        self.LabelCraftUI.cbx_RotoOutput.addItems(valid_layers)

        output_state = self.node['output'].value()
        self.LabelCraftUI.cbx_RotoOutput.setCurrentText(output_state)

        self.LabelCraftUI.cbx_RotoPremult.addItems(valid_layers)

        premult_state = self.node['premultiply'].value()
        self.LabelCraftUI.cbx_RotoPremult.setCurrentText(premult_state)

        clip_options = self.node['cliptype'].values()
        self.LabelCraftUI.cbx_RotoCliptype.addItems(clip_options)

        clip_state = self.node['cliptype'].value()
        self.LabelCraftUI.cbx_RotoCliptype.setCurrentText(clip_state)

        # set signals
        self.LabelCraftUI.cbx_RotoOutput.currentTextChanged.connect(self.change_output)
        self.LabelCraftUI.cbx_RotoPremult.currentTextChanged.connect(self.change_premult)
        self.LabelCraftUI.cbx_RotoCliptype.currentTextChanged.connect(self.change_cliptype)
        self.LabelCraftUI.ckx_RotoReplace.stateChanged.connect(self.change_replace)

    def change_output(self):
        new_output = str(self.LabelCraftUI.cbx_RotoOutput.currentText())
        self.node['output'].setValue(new_output)

    def change_premult(self):
        new_premult = str(self.LabelCraftUI.cbx_RotoPremult.currentText())
        self.node['premultiply'].setValue(new_premult)

    def change_cliptype(self):
        new_cliptype = str(self.LabelCraftUI.cbx_RotoCliptype.currentText())
        self.node['cliptype'].setValue(new_cliptype)

    def change_replace(self):
        new_replace_state = self.LabelCraftUI.ckx_RotoReplace.checkState()
        self.node['replace'].setValue(new_replace_state)

    # Switch/ Dissolve Class function
    def switch_class(self):
        self.LabelCraftUI.grp_Switch.setVisible(True)
        self.LabelCraftUI.grp_Switch.setTitle('{} knobs'.format(self.node.Class()))
        self.LabelCraftUI.cbx_SwitchExpression.setVisible(False)
        # self.SmartLabelUI.cbx_SwitchExpression.addItems(WHICH_EXPRESSIONS)

        expression_state = 'inrange'
        standard_value_a = nuke.frame()
        standard_value_b = nuke.frame() + 24

        self.LabelCraftUI.spn_SwitchValueA.setVisible(False)
        self.LabelCraftUI.spn_SwitchValueA.setRange(1, 1000000)
        self.LabelCraftUI.spn_SwitchValueA.setValue(standard_value_a)
        self.LabelCraftUI.spn_SwitchValueB.setVisible(False)
        self.LabelCraftUI.spn_SwitchValueB.setRange(1, 1000000)
        self.LabelCraftUI.spn_SwitchValueB.setValue(standard_value_b)

        if self.LabelCraftUI.ckx_SwitchExpression.checkState():
            self.LabelCraftUI.edt_SwitchWhich.setEnabled(False)
            self.LabelCraftUI.cbx_SwitchExpression.setEnabled(True)
            self.LabelCraftUI.spn_SwitchValueA.setEnabled(True)
            self.LabelCraftUI.spn_SwitchValueA.setVisible(True)
            if expression_state.startswith('inrange'):
                self.LabelCraftUI.spn_SwitchValueB.setEnabled(True)
                self.LabelCraftUI.spn_SwitchValueB.setVisible(True)
        else:
            self.LabelCraftUI.edt_SwitchWhich.setEnabled(True)
            self.LabelCraftUI.cbx_SwitchExpression.setEnabled(False)

    # Log2Lin/ OCIOLogConvert Class function
    def log2lin_class(self):
        self.LabelCraftUI.grp_Colorspaces.setVisible(True)
        self.LabelCraftUI.grp_Colorspaces.setTitle('{} knob'.format(self.node.Class()))

        self.LabelCraftUI.lbl_ColorValueB.setVisible(False)
        self.LabelCraftUI.cbx_ColorValueB.setVisible(False)
        self.LabelCraftUI.btn_ColorspaceSwap.setVisible(False)

        self.current_node_class = 'log'
        self.LabelCraftUI.lbl_ColorValueA.setVisible(True)
        self.LabelCraftUI.lbl_ColorValueA.setText('operation')

        operation_state = str(self.node['operation'].value())
        operation_options = self.node['operation'].values()

        self.LabelCraftUI.cbx_ColorValueA.setVisible(True)
        self.LabelCraftUI.cbx_ColorValueA.addItems(operation_options)
        self.LabelCraftUI.cbx_ColorValueA.setCurrentText(operation_state)

        self.LabelCraftUI.cbx_ColorValueA.currentTextChanged.connect(self.log_change)

    def log_change(self):
        self.node['operation'].setValue(str(self.LabelCraftUI.cbx_ColorValueA.currentText()))

    # OCIOColorspace/ Colorspace Class function
    def colorspace_class(self):
        self.LabelCraftUI.grp_Colorspaces.setVisible(True)
        self.LabelCraftUI.grp_Colorspaces.setTitle('{} knobs'.format(self.node.Class()))

        # self.LabelCraftUI.lbl_ColorValueA.setVisible(False)
        # self.LabelCraftUI.lbl_ColorValueB.setVisible(False)
        #
        # self.LabelCraftUI.cbx_ColorValueA.setVisible(False)
        # self.LabelCraftUI.cbx_ColorValueB.setVisible(False)
        # self.LabelCraftUI.btn_ColorspaceSwap.setVisible(False)

        if self.node.Class() == 'OCIOColorSpace':
            self.current_node_class = 'OCIOColorSpace'
            in_colorspace = int(self.node['in_colorspace'].getValue())
            out_colorspace = int(self.node['out_colorspace'].getValue())
            colorspace_options = self.node['in_colorspace'].values()

        if self.node.Class() == 'Colorspace':
            in_colorspace = int(self.node['colorspace_in'].getValue())
            out_colorspace = int(self.node['colorspace_out'].getValue())
            colorspace_options = self.node['colorspace_in'].values()

        cleanup_list = []
        for item in colorspace_options:
            if re.findall('\\t', item):
                g = item.split('\t')[1]
                cleanup_list.append(g)
            else:
                cleanup_list.append(item)

        self.LabelCraftUI.lbl_ColorValueA.setVisible(False)
        self.LabelCraftUI.lbl_ColorValueB.setVisible(False)

        self.LabelCraftUI.cbx_ColorValueA.setVisible(True)
        self.LabelCraftUI.cbx_ColorValueB.setVisible(True)
        self.LabelCraftUI.btn_ColorspaceSwap.setVisible(True)

        self.LabelCraftUI.cbx_ColorValueA.addItems(cleanup_list)
        self.LabelCraftUI.cbx_ColorValueA.setCurrentIndex(in_colorspace)

        self.LabelCraftUI.cbx_ColorValueB.addItems(cleanup_list)
        self.LabelCraftUI.cbx_ColorValueB.setCurrentIndex(out_colorspace)

        self.LabelCraftUI.cbx_ColorValueA.currentTextChanged.connect(self.change_colorspace)
        self.LabelCraftUI.cbx_ColorValueB.currentTextChanged.connect(self.change_colorspace)
        self.LabelCraftUI.btn_ColorspaceSwap.clicked.connect(self.swap_colorspace)

    def change_colorspace(self):
        if self.node.Class() == 'OCIOColorSpace':
            self.node['in_colorspace'].setValue(str(self.LabelCraftUI.cbx_ColorValueA.currentText()))
            self.node['out_colorspace'].setValue(str(self.LabelCraftUI.cbx_ColorValueB.currentText()))

        elif self.node.Class() == 'Colorspace':
            self.node['colorspace_in'].setValue(str(self.LabelCraftUI.cbx_ColorValueA.currentIndex()))
            self.node['colorspace_out'].setValue(str(self.LabelCraftUI.cbx_ColorValueB.currentIndex()))

    def swap_colorspace(self):
        value_a = str(self.LabelCraftUI.cbx_ColorValueA.currentText())
        value_b = str(self.LabelCraftUI.cbx_ColorValueB.currentText())
        self.LabelCraftUI.cbx_ColorValueA.setCurrentText(value_b)
        self.LabelCraftUI.cbx_ColorValueB.setCurrentText(value_a)

    # Text2 Class
    def text_class(self):
        self.LabelCraftUI.lbl_NodeLabel.setText('message')

        message = self.node['message'].value()
        self.LabelCraftUI.edt_NodeLabel.setText(message)

        self.LabelCraftUI.fnt_FontFace.setFontFilters(QFontComboBox.ProportionalFonts)

        self.LabelCraftUI.grp_Dot.setVisible(True)
        self.LabelCraftUI.grp_Dot.setTitle('Text options')

        self.LabelCraftUI.edt_NodeLabel.textChanged.connect(self.change_message)
        self.LabelCraftUI.fnt_FontFace.currentFontChanged.connect(self.change_font)

    def change_message(self):
        new_label = self.LabelCraftUI.edt_NodeLabel.toPlainText()
        self.node['message'].setValue(new_label)

    def change_font(self):
        font = self.LabelCraftUI.fnt_FontFace.currentFont().family()
        print(font)
        self.node['font'].setValue(font, 'Regular')

    # Dot/ Backdrop/ StickyNote Class function
    def info_class(self):
        self.LabelCraftUI.grp_Info.setVisible(True)
        self.LabelCraftUI.grp_Info.setTitle('{} knobs'.format(self.node.Class()))

        # self.LabelCraftUI.fnt_FontFace.setFontFilters(QFontComboBox.NonScalableFonts)

        self.LabelCraftUI.lbl_InfoAlign.setVisible(False)
        self.LabelCraftUI.cbx_InfoAlign.setVisible(False)

        self.LabelCraftUI.lbl_InfoIcon.setVisible(False)
        self.LabelCraftUI.cbx_InfoIcon.setVisible(False)

        self.LabelCraftUI.lbl_InfoZOrder.setVisible(False)
        self.LabelCraftUI.spn_InfoZOrder.setVisible(False)

        note_font_state = self.node['note_font'].value()
        note_size_state = self.node['note_font_size'].value()

        if 'Bold' in note_font_state:
            self.LabelCraftUI.ckx_InfoBold.setChecked(True)
            note_font_state = note_font_state.replace('Bold', '')

        if 'Italic' in note_font_state:
            self.LabelCraftUI.ckx_InfoItalic.setChecked(True)
            note_font_state = note_font_state.replace('Italic', '')

        self.LabelCraftUI.fnt_FontFace.setCurrentFont(note_font_state)
        self.LabelCraftUI.spn_InfoFontSize.setRange(5, 350)
        self.LabelCraftUI.spn_InfoFontSize.setValue(note_size_state)

        if self.current_node_class in ('backdropnode', 'stickynote'):
            self.LabelCraftUI.lbl_InfoAlign.setVisible(True)
            self.LabelCraftUI.cbx_InfoAlign.setVisible(True)
            self.LabelCraftUI.lbl_InfoIcon.setVisible(True)
            self.LabelCraftUI.cbx_InfoIcon.setVisible(True)

            self.LabelCraftUI.cbx_InfoAlign.addItems(['left', 'center'])
            self.LabelCraftUI.cbx_InfoAlign.setCurrentText(self.align_state)
            self.LabelCraftUI.cbx_InfoIcon.addItems(ICON_SELECTION)
            self.LabelCraftUI.cbx_InfoIcon.setCurrentText(self.icon_state)

            self.LabelCraftUI.cbx_InfoAlign.currentTextChanged.connect(self.change_label)
            self.LabelCraftUI.cbx_InfoIcon.currentTextChanged.connect(self.change_label)

        self.LabelCraftUI.fnt_FontFace.currentFontChanged.connect(self.change_font_family)
        self.LabelCraftUI.spn_InfoFontSize.valueChanged.connect(self.change_font_size)
        self.LabelCraftUI.ckx_InfoBold.stateChanged.connect(self.change_label)
        self.LabelCraftUI.ckx_InfoItalic.stateChanged.connect(self.change_label)
        self.LabelCraftUI.btn_FontColor.clicked.connect(self.change_font_color)

    def get_html(self):

        align_pattern = r'(<left>|<center>|<right>)'
        bold_pattern = r'(<b>)'
        italic_pattern = r'(<i>)'
        img_pattern = r'(?P<icon><img .*?>)'
        png_pattern = r'"(.*?.png)'

        alignment = None
        icon = None

        align_search = re.match(align_pattern, self.current_label)
        bold_search = re.match(bold_pattern, self.current_label)
        italic_search = re.match(italic_pattern, self.current_label)
        icon_search = re.findall(img_pattern, self.current_label)
        png_search = re.findall(png_pattern, self.current_label)

        if align_search:
            self.current_label = re.sub(align_pattern, '', self.current_label)
            alignment = align_search.group().replace('<', '').replace('>', '')

        if bold_search:
            self.current_label = re.sub(bold_pattern, '', self.current_label)
            alignment = bold_search.group().replace('<', '').replace('>', '')

        if italic_search:
            self.current_label = re.sub(italic_pattern, '', self.current_label)
            alignment = italic_search.group().replace('<', '').replace('>', '')

        if icon_search:
            icon = png_search[0].replace('.png', '')
            self.current_label = re.sub(img_pattern, '', self.current_label)

        return alignment, icon

    def dot_class(self):
        self.LabelCraftUI.grp_Dot.setVisible(True)
        self.LabelCraftUI.grp_Dot.setTitle('Dot options')

        current_font = int(self.node['note_font_size'].value())
        self.LabelCraftUI.spn_DotFontSize.setValue(current_font)

        current_note_font = self.node['note_font'].value()
        bold = re.findall('Bold', current_note_font)
        italic = re.findall('Italic', current_note_font)

        if bold:
            self.LabelCraftUI.ckx_InfoBold.setChecked(True)
        if italic:
            self.LabelCraftUI.ckx_InfoItalic.setChecked(True)

        # Signals
        self.LabelCraftUI.spn_DotFontSize.valueChanged.connect(self.change_dot)
        self.LabelCraftUI.ckx_InfoBold.stateChanged.connect(self.change_bold)
        self.LabelCraftUI.ckx_InfoItalic.stateChanged.connect(self.change_italic)

    def change_font_family(self):
        new_font = str(self.LabelCraftUI.fnt_FontFace.currentFont().family())
        self.node['note_font'].setValue(new_font)

    def change_font_size(self):
        self.node['note_font_size'].setValue(self.LabelCraftUI.spn_InfoFontSize.value())

    def change_font_color(self):
        old_color = self.node['note_font_color'].value()
        new_color = nuke.getColor(old_color)
        self.node['note_font_color'].setValue(new_color)

    # Filter Class
    def filter_class(self):
        pass

    @staticmethod
    def get_selection():
        nodes = nuke.selectedNodes()
        if len(nodes) == 1:
            return nuke.selectedNode()
        else:
            if len(nodes) == 0:
                print('Please, select one node!')
            else:
                print('Please, select only one node!')
            return None

    def edit_node(self):
        """
            This function checks the node's class, calls the specific function,
            and updates the node's parameters accordingly.
        """

        node = self.get_selection()
        if not node:
            return

        self.node = node

        self.current_node_class = self.node.Class().lower()

        self.label_knob(self.node)
        self.common_knobs(self.node)

        if self.node.Class() in ('Tracker4', 'Tracker3'):
            self.current_node_class = 'tracker'
            self.tracker_class()

        elif self.node.Class() == 'Read':
            self.current_node_class = 'read'
            self.read_class()

        elif self.node.Class() in ('Shuffle', 'Shuffle2'):
            self.current_node_class = self.node.Class().lower()
            self.shuffle_class()

        elif self.node.Class() in ('Merge2', 'ChannelMerge', 'Keymix'):
            self.current_node_class = self.node.Class().lower()
            self.merge_class()

        elif self.node.Class() in ('Roto', 'RotoPaint'):
            self.current_node_class = 'roto'
            self.roto_class()

        elif self.node.Class() in ('BackdropNode', 'StickyNote', 'Dot'):
            self.current_node_class = self.node.Class().lower()
            self.info_class()

        elif self.node.Class() in ('Dissolve', 'Switch'):
            self.current_node_class = 'switch'
            self.switch_class()

        elif self.node.Class() in ('Log2Lin', 'OCIOLogConvert'):
            self.current_node_class = 'log2lin'
            self.log2lin_class()

        elif self.node.Class() in ('Colorspace', 'OCIOColorSpace'):
            self.current_node_class = 'colorspace'
            self.colorspace_class()

        # elif self.node.Class() == 'Text2':
        #     self.current_node_class = 'text'
        #     self.text_class()

        # elif self.node.Class() == 'Dot':
        #     self.current_node_class = 'dot'
        #     self.dot_class()

        else:
            for knob in self.node.knobs():
                if knob in ('size', 'defocus'):
                    self.current_node_class = knob
                    self.filter_class()

        # resize and show Widget Window
        self.LabelCraftUI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)
        self.LabelCraftUI.move(QtGui.QCursor.pos() + QtCore.QPoint())
        # self.LabelCraftUI.move(1600, 900)
        self.LabelCraftUI.edt_NodeLabel.setFocusPolicy(Qt.StrongFocus)
        self.LabelCraftUI.edt_NodeLabel.setFocus()
        self.LabelCraftUI.adjustSize()
        self.LabelCraftUI.show()


def edit_label():
    global runTool
    runTool = LabelCraft()
    runTool.edit_node()


if __name__ == '__main__':
    edit_label()
