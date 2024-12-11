__title__ = 'LabelCraft'
__author__ = 'Luciano Cequinel'
__contact__ = 'lucianocequinel@gmail.com'
__website__ = 'https://www.cequinavfx.com/'
__website_blog__ = 'https://www.cequinavfx.com/blog/'
__version__ = '1.0.11'
__release_date__ = 'December, 11 2024'
__license__ = 'MIT'

import re
import nuke
import random
import os.path

from PySide2 import QtUiTools, QtCore, QtGui
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QFontComboBox, QStyleFactory, QMenu

from LabelCraft_customizables import (label_presets,
                                      icon_selection,
                                      dissolve_expressions,
                                      switch_expressions)


# Global Functions
def get_selection():
    """
    Retrieve the selected node in Nuke.

    Returns:
        node: The selected Nuke node, or None if selection is invalid.
    """
    nodes = nuke.selectedNodes()
    if len(nodes) == 1:
        return nuke.selectedNode()
    elif len(nodes) == 0:
        print('Please, select something!')
    else:
        print('Please, select only one node!')
    return None


def split_html(html_tags):
    """
    Parse HTML tags from a label and extract alignment, bold, italic, and icon attributes.

    Args:
        html_tags (str): The HTML content to parse.

    Returns:
        dict: Parsed HTML attributes {align, bold, italic, icon}.
    """
    align_pattern = r'(<p align=\"(?P<align>left|center|right)\">)'
    bold_pattern = r'(?P<bold><b>)'
    italic_pattern = r'(?P<italic><i>)'
    icon_pattern = r'(src ?= ?\"(?P<icon>.*?).png\")'

    # Set standard values to use them if the equivalent is not found in the string
    align = 'center'
    icon = "none"

    align_search = re.search(align_pattern, html_tags)
    if align_search:
        align = align_search.group('align')

    bold_search = re.search(bold_pattern, html_tags)
    bold = bool(bold_search)

    italic_search = re.search(italic_pattern, html_tags)
    italic = bool(italic_search)

    icon_search = re.search(icon_pattern, html_tags)
    if icon_search:
        icon = icon_search.group('icon')

    return {'align': align,
            'bold': bold,
            'italic': italic,
            'icon': icon}


def split_label(current_label):
    """
    Split a label into its HTML tags and text content.

    Args:
        current_label (str): The label to split.

    Returns:
        tuple: (dict, str) where dict contains HTML attributes and str is label text.
    """
    html_pattern = r'(?P<HTML>\<.*\>)(?P<label>.*)'
    html_search = re.search(html_pattern, current_label)
    if html_search:
        html_tags = split_html(html_search.group('HTML'))
        return html_tags, html_search.group('label')

    else:
        return ({'align': 'center',
                 'bold': True,
                 'italic': True,
                 'icon': "none"},
                current_label)


def get_layers(node):
    """
    Retrieve all layers from a given Nuke node.

    Args:
        node: The Nuke node to analyze.

    Returns:
        list: Sorted list of layers available in the node.
    """
    node_layers = nuke.layers(node)
    return sorted(node_layers)


def generate_random_color():
    COLOR_RANGE = (0.1, 0.8)
    red = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    green = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    blue = random.uniform(COLOR_RANGE[0], COLOR_RANGE[1])
    return int('{:02x}{:02x}{:02x}ff'.format(int(red * 255), int(green * 255), int(blue * 255)), 16)


class LabelCraft:
    def __init__(self):
        """
            Start UI
        """
        package_path = os.path.dirname(__file__)
        ui_path = os.path.join(package_path, __title__ + '.ui')

        self.LabelCraftUI = QtUiTools.QUiLoader().load(ui_path)
        self.LabelCraftUI.setWindowTitle(__title__)
        self.LabelCraftUI.setStyle(QStyleFactory.create('Fusion'))

        ss_file = os.path.join(package_path, 'LabelCraft_stylesheet.css')
        with open(ss_file, "r") as style_sheet:
            qss_style_content = style_sheet.read()

        self.LabelCraftUI.setStyleSheet(qss_style_content)

        # style_sheet_path = '/'.join([package_path, 'LabelCraft_stylesheet.qss'])
        # self.LabelCraftUI.setStyleSheet(style_sheet_path)

        # create Class attributes
        self.node = None
        self.current_label = None
        self.html_tags = {'align': 'center',
                          'bold': True,
                          'italic': True,
                          'icon': 'none'}
        self.current_node_class = 'none'
        self.presets = None

        self._initialize_ui()

    def _initialize_ui(self):
        """
        Set up UI components and default visibility.
        """

        _credits = ('<font size=2 color=slategrey>'
                    '<a href="{}" style="color:salmon">Label Craft</a> v{}'
                    ' - created by <a href="{}" style="color:salmon">{}</a>').format(__website_blog__,
                                                                                     __version__,
                                                                                     __website__,
                                                                                     __author__)

        self.LabelCraftUI.lbl_credits.setText(_credits)

        # Loop through all groups to make them invisible
        class_groups = [
            'grp_Read', 'grp_Roto', 'grp_Tracker', 'grp_Merge', 'grp_Info',
            'grp_Filter', 'grp_Switch', 'grp_Colorspaces'
            ]
        for _class in class_groups:
            getattr(self.LabelCraftUI, _class).setVisible(False)

        self.LabelCraftUI.btn_OK.setVisible(False)
        self.LabelCraftUI.btn_Discard.setVisible(False)

    # Label Knob
    def label_knob(self, node):
        if self.current_node_class in ('backdropnode', 'stickynote'):
            self.html_tags, self.current_label = split_label(node['label'].value())
        else:
            self.current_label = node['label'].value()

        if not self.current_label:
            self.LabelCraftUI.edt_NodeLabel.setPlaceholderText("Right-click to select a preset label")
        else:
            self.LabelCraftUI.edt_NodeLabel.setText(self.current_label)

        self.LabelCraftUI.edt_NodeLabel.selectAll()
        self.LabelCraftUI.edt_NodeLabel.setTabChangesFocus(True)

        self.LabelCraftUI.edt_NodeLabel.setFocusPolicy(Qt.StrongFocus)
        self.LabelCraftUI.edt_NodeLabel.setFocus()

        self.LabelCraftUI.edt_NodeLabel.textChanged.connect(self.update_label)
        self.LabelCraftUI.btn_NodeColor.clicked.connect(lambda: self.update_node_color('get'))
        self.LabelCraftUI.btn_random_color.clicked.connect(lambda: self.update_node_color('random'))

        self.LabelCraftUI.edt_NodeLabel.setContextMenuPolicy(Qt.CustomContextMenu)
        self.LabelCraftUI.edt_NodeLabel.customContextMenuRequested.connect(self.show_label_context_menu)

    def show_label_context_menu(self):
        self.presets = []
        if self.current_node_class in label_presets.keys():
            self.presets = label_presets[self.current_node_class]

            context_menu = QMenu(self.LabelCraftUI.edt_NodeLabel)

            # Add preset actions
            for preset in self.presets:
                action = context_menu.addAction(preset)
                action.triggered.connect(lambda checked=False, p=preset: self.insert_preset_text(p))

            # Show the context menu at the cursor position
            p = QtCore.QPoint()
            p.setX(QtGui.QCursor.pos().x())
            p.setY(QtGui.QCursor.pos().y())
            context_menu.exec_(p)

    def insert_preset_text(self, preset_text):
        cursor = self.LabelCraftUI.edt_NodeLabel.textCursor()
        cursor.insertText(preset_text)
        self.LabelCraftUI.edt_NodeLabel.setTextCursor(cursor)

    def update_label(self):
        new_label = self.LabelCraftUI.edt_NodeLabel.toPlainText()

        if self.current_node_class in ('backdropnode', 'stickynote', 'dot'):
            encode_label = new_label.encode('ascii', errors='ignore').decode('utf-8')
            label_data = {'label'   : encode_label,
                          'icon'    : '',
                          'bold'    : '',
                          'italic'  : '',
                          'align'   : ''}

            new_align = '<p align="{}">'.format(str(self.LabelCraftUI.cbx_InfoAlign.currentText()))
            new_icon = str(self.LabelCraftUI.cbx_InfoIcon.currentText())

            label_data['align'] = new_align

            if new_icon == 'none':
                label_data['icon'] = ''
            else:
                label_data['icon'] = '<img src="{}.png" width="48">'.format(new_icon)

            if self.LabelCraftUI.ckx_InfoBold.checkState():
                label_data['bold'] = '<b>'

            if self.LabelCraftUI.ckx_InfoItalic.checkState():
                label_data['italic'] = '<i>'

            if self.current_node_class == 'dot':
                info_label = '{bold}{italic}{label}'.format(**label_data)
            else:
                info_label = '{align}{bold}{italic}{icon}{label}'.format(**label_data)

            self.node['label'].setValue(info_label)

        else:
            self.node['label'].setValue(new_label)

    def update_node_color(self, method):
        old_color = self.node['tile_color'].value()
        new_color = generate_random_color()
        if method == 'get':
            new_color = nuke.getColor(old_color)

        self.node['tile_color'].setValue(new_color)

    # Common Knobs (HideInput, PostageStamp, Bookmark)
    def common_knobs(self, node):
        self.LabelCraftUI.ckx_HideInput.setVisible(False)
        self.LabelCraftUI.ckx_PostageStamp.setVisible(False)
        self.LabelCraftUI.ckx_Bookmark.setVisible(False)

        if 'hide_input' in node.knobs():
            hide_input_state = node['hide_input'].value()
            self.LabelCraftUI.ckx_HideInput.setVisible(True)
            self.LabelCraftUI.ckx_HideInput.setChecked(hide_input_state)

        if 'postage_stamp' in node.knobs():
            postagestamp_state = node['postage_stamp'].value()
            self.LabelCraftUI.ckx_PostageStamp.setVisible(True)
            self.LabelCraftUI.ckx_PostageStamp.setChecked(postagestamp_state)

        if 'bookmark' in node.knobs():
            bookmark_state = node['bookmark'].value()
            self.LabelCraftUI.ckx_Bookmark.setVisible(True)
            self.LabelCraftUI.ckx_Bookmark.setChecked(bookmark_state)

        # Signals
        self.LabelCraftUI.ckx_HideInput.stateChanged.connect(self.update_hide_input_knob)
        self.LabelCraftUI.ckx_PostageStamp.stateChanged.connect(self.update_postagestamp_knob)
        self.LabelCraftUI.ckx_Bookmark.stateChanged.connect(self.update_bookmark_knob)

    def update_hide_input_knob(self):
        self.node['hide_input'].setValue(self.LabelCraftUI.ckx_HideInput.checkState())

    def update_postagestamp_knob(self):
        self.node['postage_stamp'].setValue(self.LabelCraftUI.ckx_PostageStamp.checkState())

    def update_bookmark_knob(self):
        self.node['bookmark'].setValue(self.LabelCraftUI.ckx_Bookmark.checkState())

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

        valid_layers = get_layers(self.node)
        self.LabelCraftUI.lbl_ReadChannels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.setVisible(True)
        self.LabelCraftUI.btn_Shuffle.setVisible(True)
        self.LabelCraftUI.cbx_Channels.addItems(valid_layers)
        self.LabelCraftUI.btn_Shuffle.clicked.connect(self.shuffle_layer)

        self.LabelCraftUI.cbx_Colorspace.currentTextChanged.connect(self.change_read_colorspace)

        self.LabelCraftUI.btn_shuffle_red.clicked.connect(lambda: self.pressed_shuffle('red'))
        self.LabelCraftUI.btn_shuffle_green.clicked.connect(lambda: self.pressed_shuffle('green'))
        self.LabelCraftUI.btn_shuffle_blue.clicked.connect(lambda: self.pressed_shuffle('blue'))
        self.LabelCraftUI.btn_shuffle_alpha.clicked.connect(lambda: self.pressed_shuffle('alpha'))
        self.LabelCraftUI.btn_shuffle_white.clicked.connect(lambda: self.pressed_shuffle('white'))
        self.LabelCraftUI.btn_shuffle_black.clicked.connect(lambda: self.pressed_shuffle('black'))

    def shuffle_class(self):
        self.LabelCraftUI.grp_Read.setVisible(True)
        self.LabelCraftUI.lbl_ReadColorspace.setVisible(False)
        self.LabelCraftUI.cbx_Colorspace.setVisible(False)

        self.LabelCraftUI.btn_Shuffle.setVisible(True)

        valid_layers = get_layers(self.node)
        self.LabelCraftUI.lbl_ReadChannels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.addItems(valid_layers)
        self.LabelCraftUI.btn_Shuffle.clicked.connect(self.shuffle_layer)

        self.LabelCraftUI.cbx_Colorspace.currentTextChanged.connect(self.change_shuffle_channel)

        self.LabelCraftUI.btn_shuffle_red.clicked.connect(lambda: self.pressed_shuffle('red'))
        self.LabelCraftUI.btn_shuffle_green.clicked.connect(lambda: self.pressed_shuffle('green'))
        self.LabelCraftUI.btn_shuffle_blue.clicked.connect(lambda: self.pressed_shuffle('blue'))
        self.LabelCraftUI.btn_shuffle_alpha.clicked.connect(lambda: self.pressed_shuffle('alpha'))
        self.LabelCraftUI.btn_shuffle_white.clicked.connect(lambda: self.pressed_shuffle('white'))
        self.LabelCraftUI.btn_shuffle_black.clicked.connect(lambda: self.pressed_shuffle('black'))

    def change_read_colorspace(self):
        self.node['colorspace'].setValue(str(self.LabelCraftUI.cbx_Colorspace.currentText()))

    def change_shuffle_channel(self):
        if self.current_node_class in ('shuffle', 'shuffle2'):
            self.node['in'].setValue(str(self.LabelCraftUI.cbx_Channels.currentText()))

    def shuffle_layer(self):
        chosen_layer = str(self.LabelCraftUI.cbx_Channels.currentText())

        if chosen_layer in ('red', 'green', 'blue', 'alpha'):
            shuffle_node = nuke.nodes.Shuffle(name="Shuffle_" + chosen_layer, inputs=[self.node])

            shuffle_node['red'].setValue(chosen_layer)
            shuffle_node['green'].setValue(chosen_layer)
            shuffle_node['blue'].setValue(chosen_layer)
            shuffle_node['alpha'].setValue(chosen_layer)

        # elif chosen_layer != 'none':
        else:
            shuffle_node = nuke.nodes.Shuffle(name="Shuffle_" + chosen_layer, inputs=[self.node])
            shuffle_node.knob("in").setValue(chosen_layer)

        self.LabelCraftUI.close()

    def pressed_shuffle(self, selected_shuffle):
        if selected_shuffle == 'alpha full white':
            selected_shuffle = 'white'
        elif selected_shuffle == 'alpha full black':
            selected_shuffle = 'black'

        if self.current_node_class == 'read':
            shuffle_node = nuke.createNode('Shuffle')
        elif self.current_node_class in ('shuffle', 'shuffle2'):
            shuffle_node = self.node

        if self.current_node_class == 'shuffle':
            shuffle_node.setName("Shuffle_{}".format(selected_shuffle.upper()), uncollide=True)
            shuffle_node['red'].setValue(selected_shuffle)
            shuffle_node['green'].setValue(selected_shuffle)
            shuffle_node['blue'].setValue(selected_shuffle)
            shuffle_node['alpha'].setValue(selected_shuffle)

        if self.current_node_class == 'shuffle2':
            # if selected_shuffle not in ('white', 'black'):
            mapped = [
                ("rgba.{}".format(selected_shuffle), "rgba.red"),
                ("rgba.{}".format(selected_shuffle), "rgba.green"),
                ("rgba.{}".format(selected_shuffle), "rgba.blue"),
                ("rgba.{}".format(selected_shuffle), "rgba.alpha"),
            ]
            if selected_shuffle == 'black':
                mapped = [
                    ("black", "rgba.red"),
                    ("black", "rgba.green"),
                    ("black", "rgba.blue"),
                    ("black", "rgba.alpha"),
                ]
            elif selected_shuffle == 'white':
                mapped = [
                    ("white", "rgba.red"),
                    ("white", "rgba.green"),
                    ("white", "rgba.blue"),
                    ("white", "rgba.alpha"),
                ]


            shuffle_node["mappings"].setValue(mapped)



        node_color = {'red': 4278190335,
                      'green': 16711935,
                      'blue': 65535,
                      'alpha': 1296911871,
                      'white': 4294967295,
                      'black': 255}

        shuffle_node['tile_color'].setValue(node_color[selected_shuffle])

        self.LabelCraftUI.close()

    # Tracker Class functions
    def tracker_class(self):
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
        self.LabelCraftUI.lbl_MergeOperation.setVisible(False)
        self.LabelCraftUI.cbx_MergeOperation.setVisible(False)
        self.LabelCraftUI.cbx_MergeOperation.addItem('no operation')
        self.LabelCraftUI.cbx_MergeOperation.setCurrentText('no operation')

        # only enable operation knob when exists
        if 'operation' in self.node.knobs():
            self.current_node_class = 'merge'
            self.LabelCraftUI.lbl_MergeOperation.setVisible(True)
            self.LabelCraftUI.cbx_MergeOperation.setVisible(True)

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
        self.LabelCraftUI.sld_Mix.setSingleStep(0.1)

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

        valid_layers = get_layers(self.node)

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
        self.node['replace'].setValue(self.LabelCraftUI.ckx_RotoReplace.checkState())

    # Switch/ Dissolve Class function
    def switch_class(self):
        self.LabelCraftUI.grp_Switch.setVisible(True)
        self.LabelCraftUI.grp_Switch.setTitle('{} knobs'.format(self.node.Class()))
        self.LabelCraftUI.cbx_SwitchExpression.setVisible(True)
        self.LabelCraftUI.cbx_SwitchExpression.setEnabled(True)

        current_which = self.node['which'].value()
        self.LabelCraftUI.edt_SwitchWhich.setText(current_which)

        expression_state = 'inrange'
        standard_value_a = nuke.frame()
        standard_value_b = nuke.frame() + 24

        self.LabelCraftUI.spn_SwitchValueA.setVisible(False)
        self.LabelCraftUI.spn_SwitchValueA.setRange(1, 1000000)
        self.LabelCraftUI.spn_SwitchValueA.setValue(standard_value_a)
        self.LabelCraftUI.spn_SwitchValueB.setVisible(False)
        self.LabelCraftUI.spn_SwitchValueB.setRange(1, 1000000)
        self.LabelCraftUI.spn_SwitchValueB.setValue(standard_value_b)

        _expressions = list(switch_expressions.keys())
        if self.current_node_class == 'dissolve':
            _expressions = list(dissolve_expressions.keys())

        self.LabelCraftUI.cbx_SwitchExpression.addItems(_expressions)

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

        self.LabelCraftUI.edt_SwitchWhich.textChanged.connect(self.which_change)

    def which_change(self):
        _which = self.LabelCraftUI.edt_SwitchWhich.text()
        print(type(_which))
        if isinstance(_which, int):
            self.node['which'].setValue(_which)
        else:
            pass

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

        self.LabelCraftUI.lbl_InfoAlign.setVisible(False)
        self.LabelCraftUI.cbx_InfoAlign.setVisible(False)

        self.LabelCraftUI.lbl_InfoIcon.setVisible(False)
        self.LabelCraftUI.cbx_InfoIcon.setVisible(False)

        self.LabelCraftUI.lbl_InfoZOrder.setVisible(False)
        self.LabelCraftUI.spn_InfoZOrder.setVisible(False)

        note_font_state = self.node['note_font'].value()
        note_size_state = self.node['note_font_size'].value()

        if self.html_tags['bold']:
            self.LabelCraftUI.ckx_InfoBold.setChecked(True)
            note_font_state = note_font_state.replace('Bold', '')
            self.node['note_font'].setValue(note_font_state)

        if self.html_tags['italic']:
            self.LabelCraftUI.ckx_InfoItalic.setChecked(True)
            note_font_state = note_font_state.replace('Italic', '')
            self.node['note_font'].setValue(note_font_state)

        self.LabelCraftUI.fnt_FontFace.setCurrentFont(note_font_state)
        self.LabelCraftUI.spn_InfoFontSize.setRange(20, 350)
        self.LabelCraftUI.spn_InfoFontSize.setSingleStep(5)
        self.LabelCraftUI.spn_InfoFontSize.setValue(note_size_state)

        if self.current_node_class in ('backdropnode', 'stickynote'):
            self.LabelCraftUI.lbl_InfoAlign.setVisible(True)
            self.LabelCraftUI.cbx_InfoAlign.setVisible(True)
            self.LabelCraftUI.lbl_InfoIcon.setVisible(True)
            self.LabelCraftUI.cbx_InfoIcon.setVisible(True)

            self.LabelCraftUI.cbx_InfoAlign.addItems(['left', 'center', 'right'])
            self.LabelCraftUI.cbx_InfoAlign.setCurrentText(self.html_tags['align'])
            self.LabelCraftUI.cbx_InfoIcon.addItems(sorted(icon_selection))
            self.LabelCraftUI.cbx_InfoIcon.setCurrentText(self.html_tags['icon'])

            self.LabelCraftUI.cbx_InfoAlign.currentTextChanged.connect(self.update_label)
            self.LabelCraftUI.cbx_InfoIcon.currentTextChanged.connect(self.update_label)

        self.LabelCraftUI.fnt_FontFace.currentFontChanged.connect(self.change_font_family)
        self.LabelCraftUI.spn_InfoFontSize.valueChanged.connect(self.change_font_size)
        self.LabelCraftUI.ckx_InfoBold.stateChanged.connect(self.update_label)
        self.LabelCraftUI.ckx_InfoItalic.stateChanged.connect(self.update_label)
        self.LabelCraftUI.btn_FontColor.clicked.connect(self.change_font_color)

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

    def change_font_family(self):
        new_font = str(self.LabelCraftUI.fnt_FontFace.currentFont().family())
        self.node['note_font'].setValue(new_font)

    def change_font_size(self):
        self.node['note_font_size'].setValue(self.LabelCraftUI.spn_InfoFontSize.value())

    def change_font_color(self):
        old_color = self.node['note_font_color'].value()
        new_color = nuke.getColor(old_color)
        self.node['note_font_color'].setValue(new_color)

    def edit_node(self):
        self.node = get_selection()
        if not self.node:
            return

        self.current_node_class = self.node.Class().lower()
        self.LabelCraftUI.grp_NodeClass.setTitle(self.node.name().lower())

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

        elif self.node.Class() in ('Log2Lin', 'OCIOLogConvert'):
            self.current_node_class = 'log2lin'
            self.log2lin_class()

        elif self.node.Class() in ('Colorspace', 'OCIOColorSpace'):
            self.current_node_class = 'colorspace'
            self.colorspace_class()

        # elif self.node.Class() in ('Dissolve', 'Switch'):
        #     self.current_node_class = self.node.Class().lower()
        #     self.switch_class()

        # else:
        #     for knob in self.node.knobs():
        #         if knob in ('size', 'defocus'):
        #             self.current_node_class = knob
        #             self.filter_class()

        # reposition, resize and show Widget Window
        self.LabelCraftUI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)

        # Re-position under mouse cursor
        self.LabelCraftUI.move(QtGui.QCursor.pos().x() - (self.LabelCraftUI.width() / 2),
                               QtGui.QCursor.pos().y())

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
