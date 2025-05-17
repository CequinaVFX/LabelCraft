"""
LabelCraft is a tool for managing and editing labels in Nuke nodes. It provides a user interface for customizing
node labels, colors, and other properties. The tool supports various node types, including Read, Shuffle, Merge, Roto,
Tracker, and more.
"""

__title__ = 'LabelCraft'
__author__ = 'Luciano Cequinel'
__contact__ = 'lucianocequinel@gmail.com'
__website__ = 'https://www.cequinavfx.com/'
__website_blog__ = 'https://www.cequinavfx.com/post/label-craft'
__version__ = '1.0.28'
__release_date__ = 'May, 17 2025'
__license__ = 'MIT'

import re
import nuke
import json
import random
import os.path

from PySide2 import QtUiTools, QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QStyleFactory, QMenu

nuke.tprint(__title__, __version__)

# Global Functions
def get_selection():
    """
    Retrieve the currently selected node in Nuke.

    Returns:
        nuke.Node or None: The selected node if exactly one node is selected,
                           None if no nodes or more than one node is selected.
    """
    nodes = nuke.selectedNodes()
    if len(nodes) == 1:
        return nuke.selectedNode()
    elif len(nodes) == 0:
        print('Please, select something!')
    else:
        print('Please, select only one node!')

    return None


def get_json_data(json_file):
    """
    Read and parse a JSON file.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON data or None.
    """
    with open(json_file, "r") as file:
        data = json.load(file)

    if data:
        return data

    return None


def extract_html_tags(html_tags):
    """
    Parse HTML tags to extract alignment, bold, italic, and icon attributes.

    Args:
        html_tags (str): A string containing HTML tags.

    Returns:
        dict: A dictionary with keys 'align', 'bold', 'italic', and 'icon'
              representing the parsed attributes.
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
    Split the current label into HTML tags and label text.

    Args:
        current_label (str): The current label string.

    Returns:
        tuple: A tuple containing a dictionary of HTML tags and the label text.
    """
    html_pattern = r"(?P<HTML>\<.*\>)(?P<label>.*)"
    html_search = re.search(html_pattern, current_label, re.DOTALL)
    if html_search:
        html_tags = extract_html_tags(html_search.group('HTML'))
        return html_tags, html_search.group('label')

    else:
        print('no html')
        return ({'align': 'center',
                 'bold': True,
                 'italic': True,
                 'icon': "none"},
                current_label)


def get_layers(node):
    """
    Get the layers of a given node.

    Args:
        node (nuke.Node): The node to get layers from.

    Returns:
        list: A sorted list of layers.
    """
    node_layers = nuke.layers(node)
    return sorted(node_layers)


def generate_random_color():
    """
    Generate a random color.

    Returns:
        int: The generated color in hexadecimal format.
    """
    color_range = (0.1, 0.8)
    red = random.uniform(color_range[0], color_range[1])
    green = random.uniform(color_range[0], color_range[1])
    blue = random.uniform(color_range[0], color_range[1])
    return int('{:02x}{:02x}{:02x}ff'.format(int(red * 255), int(green * 255), int(blue * 255)), 16)


class LabelCraft:
    """
    LabelCraft class for managing and editing labels in Nuke nodes.
    """
    def __init__(self):
        """
        Initialize the LabelCraft UI.
        """

        package_path = os.path.dirname(__file__)
        ui_path = os.path.join(package_path, '{}.ui'.format(__title__))

        self.LabelCraftUI = QtUiTools.QUiLoader().load(ui_path)
        self.LabelCraftUI.setWindowTitle(__title__)
        self.LabelCraftUI.setStyle(QStyleFactory.create('Fusion'))

        ss_file = os.path.join(package_path, 'LabelCraft_stylesheet.css')
        with open(ss_file, "r") as style_sheet:
            qss_style_content = style_sheet.read()

        self.LabelCraftUI.setStyleSheet(qss_style_content)

        _json = os.path.join(package_path, 'LabelCraft_customizables.json')
        self.data = get_json_data(json_file=_json)

        self.label_presets = self.data.get('label_presets')
        self.disable_expressions = self.data.get('tcl_expressions') # ['disable']
        self.tcl_expressions = self.data.get('tcl_expressions')
        self.icon_selection = self.data.get('icon_selection')

        # create Class attributes
        self.node = None
        self.current_label = None
        self.html_tags = {'align': 'center',
                          'bold': True,
                          'italic': True,
                          'icon': 'none'}
        self.current_node_class = 'none'
        self.presets_label_knob = None
        self.presets_which_knob = None
        self.presets_disable_knob = None

        self._initialize_ui()

    def _initialize_ui(self):
        """
        Set up UI components and default visibility.
        """

        _credits = ('<font size=2 color=slategrey>'
                    '<a href="{}" style="color:#ff4242;">Label Craft</a> v {}'
                    ' - created by <a href="{}"style="color:#ff4242;">{}</a>').format(__website_blog__,
                                                                                      __version__,
                                                                                      __website__,
                                                                                      __author__)

        self.LabelCraftUI.lbl_credits.setText(_credits)
        self.LabelCraftUI.lbl_credits.setOpenExternalLinks(True)
        self.LabelCraftUI.lbl_credits.setTextInteractionFlags(self.LabelCraftUI.lbl_credits.textInteractionFlags() |
                                                              self.LabelCraftUI.lbl_credits.openExternalLinks())

        # Loop through all groups to make them invisible
        for child in self.LabelCraftUI.findChildren(QtWidgets.QWidget):
            if child.objectName().startswith('grp_'):
                child.setVisible(False)

    # Label Knob
    def label_knob(self, node):
        """
        Set up the label knob for the given node.

        Args:
            node (nuke.Node): The node to set up the label knob for.
        """

        if self.current_node_class in ('backdropnode', 'stickynote', 'dot'):
            self.html_tags, self.current_label = split_label(node['label'].value())
        else:
            self.current_label = node['label'].value()

        if not self.current_label:
            _placeholder = "Write a label to your node"
            if self.current_node_class in self.label_presets.keys():
                _placeholder = "Right-click to select a preset label"
            self.LabelCraftUI.edt_NodeLabel.setPlaceholderText(_placeholder)
        else:
            self.LabelCraftUI.edt_NodeLabel.setText(self.current_label)

        _tooltip = self.node['label'].tooltip()
        self.LabelCraftUI.edt_NodeLabel.setToolTip(_tooltip)

        self.LabelCraftUI.edt_NodeLabel.selectAll()
        self.LabelCraftUI.edt_NodeLabel.setTabChangesFocus(True)

        self.LabelCraftUI.edt_NodeLabel.setFocusPolicy(Qt.StrongFocus)
        self.LabelCraftUI.edt_NodeLabel.setFocus()

        self.LabelCraftUI.edt_NodeLabel.textChanged.connect(self.update_label_text)
        self.LabelCraftUI.btn_NodeColor.clicked.connect(lambda: self.update_node_color('get'))
        self.LabelCraftUI.btn_random_color.clicked.connect(lambda: self.update_node_color('random'))

        self.LabelCraftUI.edt_NodeLabel.setContextMenuPolicy(Qt.CustomContextMenu)
        self.LabelCraftUI.edt_NodeLabel.customContextMenuRequested.connect(self.show_label_context_menu)

    def show_label_context_menu(self):
        """
        Show the context menu for label presets.
        """
        context_menu = QMenu(self.LabelCraftUI.edt_NodeLabel)

        save_action = context_menu.addAction('save preset')
        save_action.triggered.connect(self.save_preset)
        context_menu.addSeparator()

        self.presets_label_knob = []
        if self.current_node_class in self.label_presets.keys():
            self.presets_label_knob = self.label_presets[self.current_node_class]
            # Add preset actions
            for preset in self.presets_label_knob:
                action = context_menu.addAction(preset)
                action.triggered.connect(lambda checked=False, p=preset: self.insert_preset_text(p))

        # Show the context menu at the cursor position
        point = QtCore.QPoint()
        point.setX(QtGui.QCursor.pos().x())
        point.setY(QtGui.QCursor.pos().y())
        context_menu.exec_(point)

    def save_preset(self):
        """
        Save the current label as a preset.
        """
        cursor = self.LabelCraftUI.edt_NodeLabel.textCursor()
        if cursor.hasSelection():
            preset = cursor.selectedText()
        else:
            preset = self.LabelCraftUI.edt_NodeLabel.toPlainText()

        if self.current_node_class in self.label_presets.keys():
            if preset not in self.label_presets[self.current_node_class]:
                print('Adding {} to {}'.format(preset, self.current_node_class))
                self.label_presets[self.current_node_class].append(preset)

                self.data['label_presets'] = self.label_presets

                # Save the updated presets to the JSON file
                with open(os.path.join(os.path.dirname(__file__), 'LabelCraft_customizables.json'), 'w') as f:
                    json.dump(self.data, f, indent=4)

        else:
            print('Creating a new entry to {} node: {}'.format(self.current_node_class, preset))
            self.label_presets[self.current_node_class] = [preset]
            self.data['label_presets'] = self.label_presets

            # Save the updated presets to the JSON file
            with open(os.path.join(os.path.dirname(__file__), 'LabelCraft_customizables.json'), 'w') as f:
                json.dump(self.data, f, indent=4)

    def insert_preset_text(self, preset_text):
        """
        Insert preset text into the label.

        Args:
            preset_text (str): The preset text to insert.
        """
        cursor = self.LabelCraftUI.edt_NodeLabel.textCursor()
        cursor.insertText(preset_text)
        self.LabelCraftUI.edt_NodeLabel.setTextCursor(cursor)

    def update_label_text(self):
        """
        Update the label text based on user input.
        """
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
        """
        Update the node color based on the specified method.
        : get (str): Get the color from the color picker.
        : random (str): Generate a random color.
        Args:
            method (str): The method to use for updating the color.
        """
        current_color = self.node['tile_color'].value()
        new_color = generate_random_color()
        if method == 'get':
            new_color = nuke.getColor(current_color)

        self.node['tile_color'].setValue(new_color)
        self.node['gl_color'].setValue(new_color)

        if 'color_group' in self.node.knobs():
            self.node['color_group'].setValue(str(new_color))

    # Common Knobs (HideInput, PostageStamp, Bookmark, Disable)
    def common_knobs(self, node):
        """
        Set up common knobs (HideInput, PostageStamp, Bookmark, Disable) for the given node.

        Args:
            node (nuke.Node): The node to set up common knobs for.
        """
        self.LabelCraftUI.ckx_HideInput.setVisible(False)
        self.LabelCraftUI.ckx_PostageStamp.setVisible(False)
        self.LabelCraftUI.ckx_Bookmark.setVisible(False)
        self.LabelCraftUI.ckx_Disable.setVisible(False)

        if 'hide_input' in node.knobs():
            hide_input_state = node['hide_input'].value()
            self.LabelCraftUI.ckx_HideInput.setVisible(True)
            self.LabelCraftUI.ckx_HideInput.setChecked(hide_input_state)
            _tooltip = ' shortcut alt + h\n {}'.format(self.node['hide_input'].tooltip())
            self.LabelCraftUI.ckx_HideInput.setToolTip(_tooltip)

        if 'postage_stamp' in node.knobs():
            postagestamp_state = node['postage_stamp'].value()
            self.LabelCraftUI.ckx_PostageStamp.setVisible(True)
            self.LabelCraftUI.ckx_PostageStamp.setChecked(postagestamp_state)
            _tooltip = ' shortcut alt + p\n {}'.format(self.node['postage_stamp'].tooltip())
            self.LabelCraftUI.ckx_PostageStamp.setToolTip(_tooltip)

        if 'bookmark' in node.knobs():
            bookmark_state = node['bookmark'].value()
            self.LabelCraftUI.ckx_Bookmark.setVisible(True)
            self.LabelCraftUI.ckx_Bookmark.setChecked(bookmark_state)
            _tooltip = ' shortcut alt + k\n {}'.format(self.node['bookmark'].tooltip())
            self.LabelCraftUI.ckx_Bookmark.setToolTip(_tooltip)

        if 'disable' in node.knobs():
            bookmark_state = node['disable'].value()
            self.LabelCraftUI.ckx_Disable.setVisible(True)
            self.LabelCraftUI.ckx_Disable.setChecked(bookmark_state)
            _tooltip = ' shortcut alt + d\n {}'.format(self.node['disable'].tooltip())
            self.LabelCraftUI.ckx_Disable.setToolTip(_tooltip)

            if any([node['disable'].isAnimated(), node['disable'].hasExpression()]):
                self.LabelCraftUI.ckx_Disable.setStyleSheet("""
                                                QCheckBox::indicator:unchecked {
                                                    background-color: rgb(55, 107, 189);
                                                    border: 1px solid black;
                                                    }
                                                """)
            else:
                self.LabelCraftUI.ckx_Disable.setStyleSheet("")

        # Signals
        self.LabelCraftUI.ckx_HideInput.stateChanged.connect(self.update_hide_input_knob)
        self.LabelCraftUI.ckx_PostageStamp.stateChanged.connect(self.update_postagestamp_knob)
        self.LabelCraftUI.ckx_Bookmark.stateChanged.connect(self.update_bookmark_knob)
        self.LabelCraftUI.ckx_Disable.stateChanged.connect(self.update_disable_knob)

        self.LabelCraftUI.ckx_Disable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.LabelCraftUI.ckx_Disable.customContextMenuRequested.connect(self.show_disable_context_menu)

    def update_hide_input_knob(self):
        """
        Update the hide input knob based on user input.
        """
        self.node['hide_input'].setValue(self.LabelCraftUI.ckx_HideInput.checkState())

    def update_postagestamp_knob(self):
        """
        Update the postage stamp knob based on user input.
        """
        self.node['postage_stamp'].setValue(self.LabelCraftUI.ckx_PostageStamp.checkState())

    def update_bookmark_knob(self):
        """
        Update the bookmark knob based on user input.
        """
        self.node['bookmark'].setValue(self.LabelCraftUI.ckx_Bookmark.checkState())

    def show_disable_context_menu(self):
        """
        Show the context menu for disable knob.
        """
        self.presets_disable_knob = self.tcl_expressions.get('disable')

        context_menu = QMenu(self.LabelCraftUI.ckx_Disable)

        # Add preset actions
        for _expr in self.presets_disable_knob:
            action = context_menu.addAction(_expr[2:])
            action.triggered.connect(lambda checked=False, p=self.presets_disable_knob[_expr]:
                                     self.insert_disable_expression(p))

        # Show the context menu at the cursor position
        p = QtCore.QPoint()
        p.setX(QtGui.QCursor.pos().x())
        p.setY(QtGui.QCursor.pos().y())
        context_menu.exec_(p)

    def insert_disable_expression(self, expression):
        """
        Insert a disable expression into the node.

        Args:
            expression (str): The expression to insert.
        """
        if expression:
            self.node['disable'].setExpression(expression)
            self.LabelCraftUI.ckx_Disable.setStyleSheet("""
                                            QCheckBox::indicator:unchecked {
                                                background-color: rgb(55, 107, 189);
                                                border: 1px solid black;
                                                }
                                            """)
        else:
            self.node['disable'].clearAnimated()
            self.node['disable'].setValue(False)
            self.LabelCraftUI.ckx_Disable.setStyleSheet("")

    def update_disable_knob(self):
        """
        Update the disable knob based on user input.
        """
        self.node['disable'].setValue(self.LabelCraftUI.ckx_Disable.checkState())

    # Read Class functions
    def read_class(self):
        """
        Set up the UI for Read nodes.
        """
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
        """
        Set up the UI for Shuffle nodes.
        """
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
        """
        Change the colorspace of the Read node.
        """
        self.node['colorspace'].setValue(str(self.LabelCraftUI.cbx_Colorspace.currentText()))

    def change_shuffle_channel(self):
        """
        Change the input channel of the Shuffle node.
        """
        if self.current_node_class in ('shuffle', 'shuffle2'):
            self.node['in'].setValue(str(self.LabelCraftUI.cbx_Channels.currentText()))

    def shuffle_layer(self):
        """
        Create a Shuffle node for the selected layer.
        """
        chosen_layer = str(self.LabelCraftUI.cbx_Channels.currentText())

        if chosen_layer in ('red', 'green', 'blue', 'alpha'):
            shuffle_node = nuke.nodes.Shuffle(name="Shuffle_" + chosen_layer, inputs=[self.node])

            shuffle_node['red'].setValue(chosen_layer)
            shuffle_node['green'].setValue(chosen_layer)
            shuffle_node['blue'].setValue(chosen_layer)
            shuffle_node['alpha'].setValue(chosen_layer)

        else:
            shuffle_node = nuke.nodes.Shuffle(name="Shuffle_" + chosen_layer, inputs=[self.node])
            shuffle_node.knob("in").setValue(chosen_layer)

        self.LabelCraftUI.close()

    def pressed_shuffle(self, selected_shuffle):
        """
        Create and configure a Shuffle node based on the selected shuffle channel.

        Args:
            selected_shuffle (str): The selected shuffle channel.
        """
        shuffle_node = self.node

        if self.current_node_class == 'read':
            shuffle_version = 'Shuffle2' if nuke.NUKE_VERSION_MAJOR > 12 else 'Shuffle'
            shuffle_node = nuke.createNode(shuffle_version)

        shuffle_node.setName("Shuffle_{}".format(selected_shuffle.upper()), uncollide=True)

        if shuffle_node.Class() == 'Shuffle':
            shuffle_node['red'].setValue(selected_shuffle)
            shuffle_node['green'].setValue(selected_shuffle)
            shuffle_node['blue'].setValue(selected_shuffle)
            shuffle_node['alpha'].setValue(selected_shuffle)

        elif shuffle_node.Class() == 'Shuffle2':
            _chan = selected_shuffle if selected_shuffle in ('white', 'black') else 'rgba.{}'.format(selected_shuffle)

            channel_mapping = [
                (_chan, "rgba.red"),
                (_chan, "rgba.green"),
                (_chan, "rgba.blue"),
                (_chan, "rgba.alpha"),
            ]

            shuffle_node["mappings"].setValue(channel_mapping)

        node_color = {'red': 4278190335,
                      'green': 16711935,
                      'blue': 65535,
                      'alpha': 1296911871,
                      'white': 4294967295,
                      'black': 255}

        shuffle_node['tile_color'].setValue(node_color[selected_shuffle])
        shuffle_node['gl_color'].setValue(node_color[selected_shuffle])

        self.LabelCraftUI.close()

    # Tracker Class functions
    def tracker_class(self):
        """
        Set up the UI for Tracker nodes.
        """
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
        """
        Retrieve and print the names of the tracks in the Tracker node.
        """
        n = self.node["tracks"].toScript()
        rows = n.split("\n")[34:]

        trackers = []
        for i in rows:
            try:
                track_name = i.split("}")[1].split("{")[0][2:-2]
                if track_name != "":
                    trackers.append(track_name)
            except Exception as error:
                print(error)
                continue

        # return trackers

    def change_reference(self):
        """
        Change the reference frame of the Tracker node.
        """
        self.node['reference_frame'].setValue(self.LabelCraftUI.spn_TrackerRefFrame.value())

    def change_transform(self):
        """
        Change the transform mode of the Tracker node.
        """
        self.node['transform'].setValue(str(self.LabelCraftUI.cbx_TrackerTransform.currentText()))

    def press_get_current_frame(self):
        """
        Set the reference frame of the Tracker node to the current frame.
        """
        self.LabelCraftUI.spn_TrackerRefFrame.setValue(nuke.frame())
        self.node['reference_frame'].setValue(nuke.frame())

    # Merge Class functions
    def merge_class(self):
        """
        Set up the UI for Merge nodes.
        """
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
            self.current_node_class = self.node.Class().lower()
            self.LabelCraftUI.lbl_MergeOperation.setVisible(True)
            self.LabelCraftUI.cbx_MergeOperation.setVisible(True)

            operation_options = self.node['operation'].values()
            self.LabelCraftUI.cbx_MergeOperation.addItems(operation_options)

            operation_state = str(self.node['operation'].value())
            self.LabelCraftUI.cbx_MergeOperation.setCurrentText(operation_state)

            _tooltip = self.node['operation'].tooltip()
            self.LabelCraftUI.cbx_MergeOperation.setToolTip(_tooltip)

        # bbox knob
        if 'bbox' in self.node.knobs():
            bbox_options = self.node['bbox'].values()
            self.LabelCraftUI.cbx_MergeBBox.addItems(bbox_options)

            bbox_state = str(self.node['bbox'].value())
            self.LabelCraftUI.cbx_MergeBBox.setCurrentText(bbox_state)

            _tooltip = self.node['bbox'].tooltip()
            self.LabelCraftUI.cbx_MergeBBox.setToolTip(_tooltip)

        # mix knob
        if 'mix' in self.node.knobs():
            mix_state = self.node['mix'].value()

            if any([self.node['mix'].isAnimated(), self.node['mix'].hasExpression()]):
                self.LabelCraftUI.lbl_Mix.setStyleSheet("""
                                                    QLabel{
                                                        background-color: rgb(55, 107, 189);
                                                        padding: 3px;
                                                        }
                                                    """)
            else:
                self.LabelCraftUI.lbl_Mix.setStyleSheet("")

            self.LabelCraftUI.spn_Mix.setRange(0, 1)
            self.LabelCraftUI.spn_Mix.setValue(mix_state)

            self.LabelCraftUI.sld_Mix.setValue(int(mix_state * 100))
            self.LabelCraftUI.sld_Mix.setRange(0, 100)
            self.LabelCraftUI.sld_Mix.setSingleStep(0.1)

            _tooltip = self.node['mix'].tooltip()
            self.LabelCraftUI.spn_Mix.setToolTip(_tooltip)
            self.LabelCraftUI.sld_Mix.setToolTip(_tooltip)

        # Signals
        self.LabelCraftUI.cbx_MergeOperation.currentTextChanged.connect(self.change_operation)
        self.LabelCraftUI.cbx_MergeBBox.currentTextChanged.connect(self.change_bbox)
        self.LabelCraftUI.spn_Mix.valueChanged.connect(self.change_spin_mix)
        self.LabelCraftUI.sld_Mix.valueChanged.connect(self.change_slider_mix)

    def change_operation(self):
        """
        Change the operation mode of the Merge node.
        """
        new_operation = str(self.LabelCraftUI.cbx_MergeOperation.currentText())
        self.node['operation'].setValue(new_operation)

    def change_bbox(self):
        """
        Change the bounding box mode of the Merge node.
        """
        new_bbox = str(self.LabelCraftUI.cbx_MergeBBox.currentText())
        self.node['bbox'].setValue(new_bbox)

    def change_spin_mix(self):
        """
        Change the mix value of the Merge node using the spin box.
        """
        new_mix = float(self.LabelCraftUI.spn_Mix.value())
        self.LabelCraftUI.sld_Mix.setValue(int(new_mix * 100))

        self.node['mix'].setValue(new_mix)

    def change_slider_mix(self):
        """
        Change the mix value of the Merge node using the slider.
        """
        new_mix = (float(self.LabelCraftUI.sld_Mix.value()) / 100)
        self.LabelCraftUI.spn_Mix.setValue(new_mix)

        self.node['mix'].setValue(new_mix)

    # Roto/ RotoPaint Class functions
    def roto_class(self):
        """
        Set up the UI for Roto and RotoPaint nodes.
        """
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

        clip_replace = self.node['replace'].value()
        self.LabelCraftUI.ckx_RotoReplace.setChecked(clip_replace)

        # set signals
        self.LabelCraftUI.cbx_RotoOutput.currentTextChanged.connect(self.change_output)
        self.LabelCraftUI.cbx_RotoPremult.currentTextChanged.connect(self.change_premult)
        self.LabelCraftUI.cbx_RotoCliptype.currentTextChanged.connect(self.change_cliptype)
        self.LabelCraftUI.ckx_RotoReplace.stateChanged.connect(self.change_replace)

    def change_output(self):
        """
        Change the output layer of the Roto node.
        """
        new_output = str(self.LabelCraftUI.cbx_RotoOutput.currentText())
        self.node['output'].setValue(new_output)

    def change_premult(self):
        """
        Change the premultiply layer of the Roto node.
        """
        new_premult = str(self.LabelCraftUI.cbx_RotoPremult.currentText())
        self.node['premultiply'].setValue(new_premult)

    def change_cliptype(self):
        """
        Change the clip type of the Roto node.
        """
        new_cliptype = str(self.LabelCraftUI.cbx_RotoCliptype.currentText())
        self.node['cliptype'].setValue(new_cliptype)

    def change_replace(self):
        """
        Change the replace knob of the Roto node.
        """
        self.node['replace'].setValue(self.LabelCraftUI.ckx_RotoReplace.checkState())

    # Switch/ Dissolve Class function
    def switch_class(self):
        """
        Set up the UI for Switch and Dissolve nodes.
        """
        self.LabelCraftUI.grp_Switch.setVisible(True)
        self.LabelCraftUI.grp_Switch.setTitle('{} knobs'.format(self.node.Class()))

        # node['which'].toScript()
        if 'which_expression' in self.node.knobs():
            current_expression = self.node['which_expression'].value()
            self.LabelCraftUI.edt_SwitchWhich.setText(current_expression)
        else:
            current_which = int(self.node['which'].value())
            self.LabelCraftUI.edt_SwitchWhich.setText(str(current_which))

        if any([self.node['which'].isAnimated(), self.node['which'].hasExpression()]):
                self.LabelCraftUI.lbl_SwitchWhich.setStyleSheet("""
                                                    QLabel{
                                                        background-color: rgb(55, 107, 189);
                                                        padding: 3px;
                                                        }
                                                    """)
        else:
            self.LabelCraftUI.lbl_SwitchWhich.setStyleSheet("")


        knobs = ['value_A', 'value_B', 'value_C', 'value_D']

        for v, knob in enumerate(knobs):
            _label_name = 'lbl_{}'.format(knob)
            _spin_name = 'spn_Switch_{}'.format(knob)

            standard_value = nuke.frame() if v == 0 else nuke.frame() + int(((nuke.root()['fps'].value() * v) / 2))

            getattr(self.LabelCraftUI, _label_name).setVisible(False)
            getattr(self.LabelCraftUI, _spin_name).setVisible(False)
            getattr(self.LabelCraftUI, _spin_name).setRange(1, 1000000)
            getattr(self.LabelCraftUI, _spin_name).setValue(standard_value)

            getattr(self.LabelCraftUI, _spin_name).valueChanged.connect(lambda value, k=knob:
                                                                        self.change_expression_value(k, value))

            if knob in self.node.knobs():
                getattr(self.LabelCraftUI, _label_name).setVisible(True)
                getattr(self.LabelCraftUI, _spin_name).setVisible(True)
                getattr(self.LabelCraftUI, _spin_name).setValue(self.node[knob].value())

        self.LabelCraftUI.edt_SwitchWhich.setContextMenuPolicy(Qt.CustomContextMenu)
        self.LabelCraftUI.edt_SwitchWhich.customContextMenuRequested.connect(self.show_expression_context_menu)
        self.LabelCraftUI.edt_SwitchWhich.textChanged.connect(self.which_change)

    def show_expression_context_menu(self):
        """
        Show the context menu for expression presets.
        """
        self.presets_which_knob = self.tcl_expressions.get(self.current_node_class)

        context_menu = QMenu(self.LabelCraftUI.edt_SwitchWhich)

        # Add preset actions
        for _name, _expression in sorted(self.presets_which_knob.items()):
            action = context_menu.addAction(_name[2:])
            action.triggered.connect(lambda checked=False, p = _expression: self.LabelCraftUI.edt_SwitchWhich.setText(p))

        # Show the context menu at the cursor position
        p = QtCore.QPoint()
        p.setX(QtGui.QCursor.pos().x())
        p.setY(QtGui.QCursor.pos().y())
        context_menu.exec_(p)

    def which_change(self):
        """
        Update the 'which' knob based on user input.
        """
        _which = self.LabelCraftUI.edt_SwitchWhich.text()

        if _which.isdigit():
            self.node['which'].clearAnimated()
            self.node['which'].setValue(_which)
            self.manage_knobs(expression='')
            self.LabelCraftUI.lbl_SwitchWhich.setStyleSheet("")
        elif _which == '':
            self.node['which'].clearAnimated()
            self.node['which'].setValue(0)
            self.manage_knobs(expression='')
            self.LabelCraftUI.lbl_SwitchWhich.setStyleSheet("")
        else:
            self.node['which'].setExpression(_which)
            self.manage_knobs(expression=_which)
            self.LabelCraftUI.lbl_SwitchWhich.setStyleSheet("""
                                                QLabel{
                                                    background-color: rgb(55, 107, 189);
                                                    padding: 3px;
                                                    }
                                                """)

    def change_expression_value(self, knob, value):
        """
        Change the value of the specified knob.

        Args:
            knob (str): The name of the knob.
            value (int): The new value for the knob.
        """
        self.node[knob].setValue(value)

    def manage_knobs(self, expression):
        """
        Manage the visibility and values of knobs based on the expression.

        Args:
            expression (str): The expression to manage knobs for.
        """
        if 'which_expression' in self.node.knobs():
            self.node['which_expression'].setValue(expression)
        elif expression:
            tab = nuke.Tab_Knob('lc_tab', 'Setup expression')
            self.node.addKnob(tab)
            expr_label = nuke.Text_Knob('which_expression', ' ', expression)
            expr_label.setVisible(False)
            self.node.addKnob(expr_label)

        knobs = ['value_A', 'value_B', 'value_C', 'value_D']
        for _knob in knobs:
            _label_name = 'lbl_{}'.format(_knob)
            _spin_name = 'spn_Switch_{}'.format(_knob)

            spinbox = getattr(self.LabelCraftUI, _spin_name)
            current_value = spinbox.value()

            if _knob in expression:
                if _knob not in self.node.knobs():
                    knob_a = nuke.Int_Knob(_knob, _knob)
                    self.node.addKnob(knob_a)

                self.node[_knob].setVisible(True)
                self.node[_knob].setValue(int(current_value))
                getattr(self.LabelCraftUI, _label_name).setVisible(True)
                getattr(self.LabelCraftUI, _spin_name).setVisible(True)

            if _knob not in expression and _knob in self.node.knobs():
                self.node[_knob].setVisible(False)
                getattr(self.LabelCraftUI, _label_name).setVisible(False)
                getattr(self.LabelCraftUI, _spin_name).setVisible(False)

    # Log2Lin/ OCIOLogConvert Class function
    def log2lin_class(self):
        """
        Set up the UI for Log2Lin and OCIOLogConvert nodes.
        """
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
        """
        Change the operation mode of the Log2Lin or OCIOLogConvert node.
        """
        self.node['operation'].setValue(str(self.LabelCraftUI.cbx_ColorValueA.currentText()))

    # Dot/ Backdrop/ StickyNote Class function
    def info_class(self):
        """
        Set up the UI for Dot, Backdrop, and StickyNote nodes.
        """
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

            if self.current_node_class == 'backdropnode':
                self.LabelCraftUI.lbl_InfoZOrder.setVisible(True)
                self.LabelCraftUI.spn_InfoZOrder.setVisible(True)
                self.LabelCraftUI.spn_InfoZOrder.setRange(-99, 99)

                _current_order = self.node['z_order'].value()
                self.LabelCraftUI.spn_InfoZOrder.setValue(_current_order)
                self.LabelCraftUI.spn_InfoZOrder.valueChanged.connect(lambda v=self.LabelCraftUI.spn_InfoZOrder.value():
                                                                      self.change_zorder(v))

            self.LabelCraftUI.cbx_InfoAlign.addItems(['left', 'center', 'right'])
            self.LabelCraftUI.cbx_InfoAlign.setCurrentText(self.html_tags['align'])
            self.LabelCraftUI.cbx_InfoIcon.addItems(sorted(self.icon_selection))
            self.LabelCraftUI.cbx_InfoIcon.setCurrentText(self.html_tags['icon'])

            self.LabelCraftUI.cbx_InfoAlign.currentTextChanged.connect(self.update_label_text)
            self.LabelCraftUI.cbx_InfoIcon.currentTextChanged.connect(self.update_label_text)

        self.LabelCraftUI.fnt_FontFace.currentFontChanged.connect(self.change_font_family)
        self.LabelCraftUI.spn_InfoFontSize.valueChanged.connect(self.change_font_size)
        self.LabelCraftUI.ckx_InfoBold.stateChanged.connect(self.update_label_text)
        self.LabelCraftUI.ckx_InfoItalic.stateChanged.connect(self.update_label_text)
        self.LabelCraftUI.btn_FontColor.clicked.connect(self.change_font_color)

    def change_font_family(self):
        """
        Change the font family of the note.
        """
        new_font = str(self.LabelCraftUI.fnt_FontFace.currentFont().family())
        self.node['note_font'].setValue(new_font)

    def change_font_size(self):
        """
        Change the font size of the note.
        """
        font_size = self.LabelCraftUI.spn_InfoFontSize.value()
        self.node['note_font_size'].setValue(font_size)

    def change_font_color(self):
        """
        Change the font color of the note.
        """
        old_color = self.node['note_font_color'].value()
        new_color = nuke.getColor(old_color)
        self.node['note_font_color'].setValue(new_color)

    def change_zorder(self, value):
        """
        Change the Z-order of the backdrop node.
        """
        self.node['z_order'].setValue(int(value))

    # ScanlineRender Class functions
    def scanline_class(self):
        """
        Set up the UI for ScanlineRender nodes.
        """
        self.LabelCraftUI.grp_Scanline.setVisible(True)
        self.LabelCraftUI.grp_Scanline.setTitle('{}'.format(self.node.Class()))

        current_state = self.node['projection_mode'].value()
        _options = self.node['projection_mode'].values()

        projection_commands = {}
        for _opt in _options:
            split = _opt.split('\t')
            if len(split) > 1:
                projection_commands[split[1]] = split[0]
            else:
                projection_commands[split[0]] = split[0]

        self.LabelCraftUI.cbx_projection_mode.addItems(projection_commands.keys())
        self.LabelCraftUI.cbx_projection_mode.setCurrentText(str(current_state))

        self.LabelCraftUI.cbx_projection_mode.currentTextChanged.connect(lambda cmd=projection_commands[self.LabelCraftUI.cbx_projection_mode.currentText()]:
                                                                         self.change_projection(cmd))

    def change_projection(self, command):
        """
        Change the projection mode of the ScanlineRender node.
        """
        self.node['projection_mode'].setValue(str(command))

    # Main Function that calls the corresponding Class
    def edit_node(self):
        """
        Edit the selected node by setting up the appropriate UI components based on the node class.
        """
        self.node = get_selection()

        if not self.node:
            return

        self.current_node_class = self.node.Class().lower()
        self.LabelCraftUI.NodeClass_group.setTitle(self.node.name().lower())

        self.label_knob(self.node)
        self.common_knobs(self.node)

        if self.node.Class() in ('Tracker4', 'Tracker3'):
            self.current_node_class = self.node.Class().lower()
            self.tracker_class()

        elif self.node.Class() == 'Read':
            self.current_node_class = self.node.Class().lower()
            self.read_class()

        elif self.node.Class() in ('Shuffle', 'Shuffle2'):
            self.current_node_class = self.node.Class().lower()
            self.shuffle_class()

        elif self.node.Class() in ('Merge2', 'ChannelMerge', 'Keymix'):
            self.current_node_class = self.node.Class().lower()
            self.merge_class()

        elif self.node.Class() in ('Roto', 'RotoPaint'):
            self.current_node_class = self.node.Class().lower()
            self.roto_class()

        elif self.node.Class() in ('BackdropNode', 'StickyNote', 'Dot'):
            self.current_node_class = self.node.Class().lower()
            self.info_class()

        elif self.node.Class() in ('Log2Lin', 'OCIOLogConvert'):
            self.current_node_class = self.node.Class().lower()
            self.log2lin_class()

        elif self.node.Class() in ('Dissolve', 'Switch'):
            self.current_node_class = self.node.Class().lower()
            self.switch_class()

        elif self.node.Class() in ('ScanlineRender', 'ScanlineRender2'):
            self.current_node_class = self.node.Class().lower()
            self.scanline_class()

        # Re-position, resize and show floating Widget Window
        self.LabelCraftUI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |
                                         QtCore.Qt.Popup)
        self.LabelCraftUI.adjustSize()

        # Get screen geometry + mouse pointer position
        screen_geometry = QtWidgets.QApplication.desktop().availableGeometry()
        cursor_pos = QtGui.QCursor.pos()
        window_width = self.LabelCraftUI.width()
        window_height = self.LabelCraftUI.height()

        # Calculate x position (prevent going off left or right side)
        x = cursor_pos.x() # - int(window_width / 2)
        if x + window_width > screen_geometry.right():
            x = screen_geometry.right() - window_width
        elif x - int(window_width / 2) < screen_geometry.left():
            x = screen_geometry.left()
        else:
            x = x - int(window_width / 2)

        # Calculate y position (prevent going off bottom)
        y = cursor_pos.y()
        if y + window_height > screen_geometry.bottom():
            y = screen_geometry.bottom() - window_height

        # Move window to calculated position
        self.LabelCraftUI.move(x, y)

        # Set Focus to the Label Box
        self.LabelCraftUI.edt_NodeLabel.setFocusPolicy(Qt.StrongFocus)
        self.LabelCraftUI.edt_NodeLabel.setFocus()

        # Resize to its contents
        self.LabelCraftUI.adjustSize()
        self.LabelCraftUI.show()


def edit_label():
    """
    Initialize and run the LabelCraft tool to edit the label of the selected node.
    """
    run_labelcraft = LabelCraft()
    run_labelcraft.edit_node()


if __name__ == '__main__':
    edit_label()
