"""
LabelCraft is a Nuke tool for editing and customizing node labels and knobs for any given node.
"""

__title__ = 'LabelCraft'
__author__ = 'Luciano Cequinel'
__website__ = 'https://www.cequinavfx.com/'
__website_blog__ = 'https://www.cequinavfx.com/post/label-craft'
__version__ = '1.4.0'
__release_date__ = 'Jan, 25 2026'
__license__ = 'MIT'

import re
import json
import random
import os.path

import nuke

from Qt import QtCore, QtGui, QtWidgets, QtCompat
from Qt.QtCore import Qt, QUrl, Signal, QObject
from Qt.QtWidgets import QStyleFactory, QMenu, QAction

nuke.tprint('\n\t', __title__, __version__, '\n')

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
    if os.path.exists(json_file):
        with open(json_file, "r") as file:
            data = json.load(file)

        return data

    return {}


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
    color_range = (0.02, 0.7)
    red = random.uniform(color_range[0], color_range[1])
    green = random.uniform(color_range[0], color_range[1])
    blue = random.uniform(color_range[0], color_range[1])
    return int('{:02x}{:02x}{:02x}ff'.format(int(red * 255), int(green * 255), int(blue * 255)), 16)


def get_html_tags(tags):
    """
    Extract tags.

    Returns:
        dict of tags
    """
    style = {
        'align': 'center',
        'bold': False,
        'italic': False,
        'icon': 'none'
    }

    open_tags = []

    for tag in tags:
        tag_type = tag.get('type', '')

        if tag.get('closing'):
            if open_tags and open_tags[-1] == tag_type:
                open_tags.pop()
        else:
            open_tags.append(tag_type)

            if 'b' in open_tags:
                style['bold'] = True
            if 'i' in open_tags:
                style['italic'] = True

            if tag_type == 'img' and 'src' in tag:
                src = tag['src']
                name = os.path.splitext(os.path.basename(src))[0]
                style['icon'] = name

            if 'align' in tag:
                style['align'] = tag['align']
            elif tag_type in ['center', 'left', 'right']:
                style['align'] = tag_type

    return {k: v for k, v in style.items()}


def html_handler(text):
    """
    Check if the string has HTML tags and separate them

    Returns:
        html_tags (dict)
        cleaned string (str)
    """

    tag_pattern = r'<(\/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>'

    tags = []
    plain_text = ""

    pos = 0
    while pos < len(text):
        match = re.search(tag_pattern, text[pos:])

        if match:
            tag_start = match.start()
            if tag_start > 0:
                plain_text += text[pos:pos + tag_start]

            is_closing = match.group(1) == '/'
            tag_name = match.group(2).lower()
            attrs_text = match.group(3).strip()

            attrs = {}
            if attrs_text:
                attr_pattern = r'([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s/>]+))'
                for attr_match in re.finditer(attr_pattern, attrs_text):
                    key = attr_match.group(1).lower()
                    value = attr_match.group(2) or attr_match.group(3) or attr_match.group(4) or ""
                    attrs[key] = value

            if is_closing:
                tags.append({'type': tag_name, 'closing': True})
            else:
                tags.append(dict({'type': tag_name}, **attrs))

            pos += match.end()
        else:
            plain_text += text[pos:]
            break

    check_tags = get_html_tags(tags)

    return check_tags, plain_text


class ColorspaceCascadingMenu(QObject, object):
    """
    Create a menu for a given QPushButton, handling weird strings and tab special characters.
    It will create a fake ComboBox/ Dropdown menu with sub-items, similar to Cascading's Nuke menu.
    """
    itemSelected = Signal(str, str)

    def __init__(self, button, button_name=None):
        """
        Initialize with an existing QPushButton

        Args:
            button: Existing QPushButton to attach menu to
        """
        QObject.__init__(self)
        self.button = button
        self.button.setObjectName(button_name)
        self._menu = None
        self._entries = []

        self.button.clicked.connect(self.show_menu)

    def set_entries(self, entries):
        """Set the list of entries (can contain both hierarchical and flat items)"""
        self._entries = entries

    def show_menu(self):
        """Show the cascading menu"""
        if not self._entries:
            return

        self._menu = self.create_menu()
        self._menu.exec_(self.button.mapToGlobal(self.button.rect().bottomLeft()))

    def build_entry_tree(self):
        """
        Build a hierarchical tree from entries.

        Supports:
        - '/' for hierarchy
        - '\\t' for description (ignored for hierarchy)

        Returns:
            dict representing a tree structure
        """
        tree = {}

        for raw in self._entries:
            if not raw:
                continue

            # Handle tab separator
            if '\t' in raw:
                entry, _desc = raw.split('\t', 1)
            else:
                entry = raw

            entry = entry.strip()
            parts = [p.strip() for p in entry.split('/')]

            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})

            # Leaf node
            node[parts[-1]] = entry

        return tree

    def add_tree_to_menu(self, menu, tree, callback):
        """
        Recursively add tree items to a QMenu.
        """
        for label in sorted(tree.keys()):
            if 'default' in label.lower():
                continue

            value = tree[label]

            if isinstance(value, dict):
                submenu = QMenu(label, menu)
                menu.addMenu(submenu)
                self.add_tree_to_menu(submenu, value, callback)
            else:
                action = QAction(label, menu)
                action.triggered.connect(
                    lambda e=value, n=self.button.objectName(): callback(e, n)
                )
                menu.addAction(action)

    def create_menu(self):
        """Create hierarchical menu from entries, supporting '/' and '\\t' separators"""
        menu = QMenu(self.button)

        tree = self.build_entry_tree()
        self.add_tree_to_menu(menu, tree, self._emit_colorspace_selection)

        return menu

    def _emit_colorspace_selection(self, item, button_name):
        """
        Emit the itemSelected signal with the selected item and button name
        Args:
            item (str): The selected item.
            button_name (str): The name of the button.
        """
        self.itemSelected.emit(item, button_name)


class LabelCraft:
    """
    LabelCraft class for managing and editing labels in Nuke nodes.
    """
    def __init__(self):
        """
        Initialize the LabelCraft Class.
        """

        package_path = os.path.dirname(__file__)
        ui_path = os.path.join(package_path, '{}.ui'.format(__title__))

        self.LabelCraftUI = QtCompat.loadUi(ui_path)

        self.LabelCraftUI.setWindowTitle(__title__)
        self.LabelCraftUI.setStyle(QStyleFactory.create('Fusion'))

        ss_file = os.path.join(package_path, 'LabelCraft_stylesheet.css')
        with open(ss_file, "r") as style_sheet:
            qss_style_content = style_sheet.read()

        self.LabelCraftUI.setStyleSheet(qss_style_content)

        self.custom_db = os.path.join(package_path, 'LabelCraft_customizables.json')
        self.data = get_json_data(json_file=self.custom_db)

        self.label_presets = self.data.get('label_presets', {})
        self.disable_expressions = self.data.get('tcl_expressions', {})
        self.tcl_expressions = self.data.get('tcl_expressions', {})
        self.icon_selection = self.data.get('icon_selection', [])

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
        Set up UI components, default visibility and draggable functionality.
        """
        self.LabelCraftUI.btn_guide.clicked.connect(self.open_guide)

        _credits = 'Label Craft v{} | created by {}'.format(__version__, __author__)

        self.LabelCraftUI.lbl_credits.setText(_credits)

        # Loop through all groups to make them invisible
        for child in self.LabelCraftUI.findChildren(QtWidgets.QWidget):
            if child.objectName().startswith('grp_'):
                child.setVisible(False)

    # Open guide
    @staticmethod
    def open_guide():
        """
        Open the LabelCraft guide in the default web browser.
        """
        import webbrowser
        webbrowser.open(__website_blog__)

    # Label Knob
    def label_knob(self, node):
        """
        Set up the label knob for the given node.

        Args:
            node (nuke.Node): The node to set up the label knob for.
        """

        self.current_label = node['label'].value()

        if self.current_node_class in ('backdropnode', 'stickynote', 'dot'):
            self.html_tags, self.current_label = html_handler(node['label'].value())

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

            # Add separator and delete submenu
            if self.presets_label_knob:
                context_menu.addSeparator()
                delete_submenu = QMenu('delete preset', context_menu)
                context_menu.addMenu(delete_submenu)

                # Add the same preset items to delete submenu
                for preset in self.presets_label_knob:
                    delete_action = delete_submenu.addAction(preset)
                    delete_action.triggered.connect(lambda checked=False, p=preset: self.delete_preset(p))


        # Show the context menu at the cursor position
        point = QtCore.QPoint()
        point.setX(QtGui.QCursor.pos().x())
        point.setY(QtGui.QCursor.pos().y())
        context_menu.exec_(point)

    def _save_db(self):
        """
        Save the current data to the custom JSON database.
        """
        with open(self.custom_db, 'w') as f:
            json.dump(self.data, f, indent=4)

    def save_preset(self):
        """
        Save the current label as a preset.
        """
        preset = self.LabelCraftUI.edt_NodeLabel.toPlainText()
        cursor = self.LabelCraftUI.edt_NodeLabel.textCursor()

        if any([preset == '', preset is None, preset.isspace()]):
            return
        elif cursor.hasSelection():
            preset = cursor.selectedText()

        if self.current_node_class in self.label_presets.keys():
            if preset not in self.label_presets[self.current_node_class]:
                print('Adding {} to {}'.format(preset, self.current_node_class))
                self.label_presets[self.current_node_class].append(preset)
                self.data['label_presets'] = self.label_presets

                # Save the updated presets to the JSON file
                self._save_db()

        else:
            print('Creating a new entry to {} node: {}'.format(self.current_node_class, preset))
            self.label_presets[self.current_node_class] = [preset]
            self.data['label_presets'] = self.label_presets

            # Save the updated presets to the JSON file
            self._save_db()

    def delete_preset(self, preset):
        """
        Delete existing preset.
        Args:
            preset:
        """
        if self.current_node_class in self.label_presets:
            if preset in self.label_presets[self.current_node_class]:
                self.label_presets[self.current_node_class].remove(preset)
                self.data['label_presets'] = self.label_presets
                self._save_db()
                print('Deleting preset:', preset)
        else:
            print('No presets found for node class.', self.current_node_class)

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
        self.LabelCraftUI.grp_Read.setTitle('{} knobs'.format(self.node.name()))

        colorspace_options = self.node['colorspace'].values()
        colorspace_state = self.node['colorspace'].value()

        self.LabelCraftUI.lbl_ReadChannels.setVisible(False)
        self.LabelCraftUI.cbx_Channels.setVisible(False)
        self.LabelCraftUI.btn_Shuffle.setVisible(False)

        valid_layers = get_layers(self.node)
        self.LabelCraftUI.lbl_ReadChannels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.setVisible(True)
        self.LabelCraftUI.btn_Shuffle.setVisible(True)
        self.LabelCraftUI.cbx_Channels.addItems(valid_layers)
        self.LabelCraftUI.btn_Shuffle.clicked.connect(self.shuffle_layer)

        self.btn_colorspace = self.LabelCraftUI.btn_Colorspace
        self.btn_colorspace.setText(colorspace_state)

        self.read_colorspace = ColorspaceCascadingMenu(self.btn_colorspace, 'ReadColorspace')
        self.read_colorspace.set_entries(colorspace_options)

        self.read_colorspace.itemSelected.connect(self.change_read_colorspace)

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
        self.LabelCraftUI.grp_Read.setTitle('{} knobs'.format(self.node.name()))

        self.LabelCraftUI.lbl_ReadColorspace.setVisible(False)
        self.LabelCraftUI.btn_Colorspace.setVisible(False)

        self.LabelCraftUI.btn_Shuffle.setVisible(True)

        valid_layers = get_layers(self.node)
        self.LabelCraftUI.lbl_ReadChannels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.setVisible(True)
        self.LabelCraftUI.cbx_Channels.addItems(valid_layers)
        self.LabelCraftUI.btn_Shuffle.clicked.connect(self.shuffle_layer)

        self.LabelCraftUI.btn_shuffle_red.clicked.connect(lambda: self.pressed_shuffle('red'))
        self.LabelCraftUI.btn_shuffle_green.clicked.connect(lambda: self.pressed_shuffle('green'))
        self.LabelCraftUI.btn_shuffle_blue.clicked.connect(lambda: self.pressed_shuffle('blue'))
        self.LabelCraftUI.btn_shuffle_alpha.clicked.connect(lambda: self.pressed_shuffle('alpha'))
        self.LabelCraftUI.btn_shuffle_white.clicked.connect(lambda: self.pressed_shuffle('white'))
        self.LabelCraftUI.btn_shuffle_black.clicked.connect(lambda: self.pressed_shuffle('black'))

    def change_read_colorspace(self, selected_item):
        """
        Change the colorspace of the Read node.
        """
        button_label = selected_item

        _parts = selected_item.split('/')
        if _parts:
            button_label = _parts[-1]

        self.btn_colorspace.setText(button_label)
        self.node['colorspace'].setValue(str(selected_item))

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
        self.LabelCraftUI.grp_Tracker.setTitle('{} knobs'.format(self.node.name()))

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
        self.LabelCraftUI.grp_Merge.setTitle('{} knobs'.format(self.node.name()))

        # assume node class as Keymix to start and avoid operation error
        self.LabelCraftUI.lbl_MergeOperation.setVisible(False)
        self.LabelCraftUI.cbx_MergeOperation.setVisible(False)
        # self.LabelCraftUI.cbx_MergeOperation.addItem('no operation')
        # self.LabelCraftUI.cbx_MergeOperation.setCurrentText('no operation')

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
        self.LabelCraftUI.grp_Roto.setTitle('{} knobs'.format(self.node.name()))

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
        self.LabelCraftUI.grp_Switch.setTitle('{} knobs'.format(self.node.name()))

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
        self.current_node_class = 'log'
        self.LabelCraftUI.grp_logtolin.setVisible(True)
        self.LabelCraftUI.grp_logtolin.setTitle('{} knobs'.format(self.node.name()))

        operation_state = str(self.node['operation'].value())
        operation_options = self.node['operation'].values()

        opposite = operation_options[1 - operation_options.index(operation_state)]

        self.LabelCraftUI.btn_swap_log.setText(opposite)

        self.LabelCraftUI.btn_swap_log.clicked.connect(lambda: self.log_change(opposite))

    def log_change(self, operation):
        """
        Change the operation mode of the Log2Lin or OCIOLogConvert node.
        """
        self.node['operation'].setValue(str(operation))
        self.log2lin_class()

    # OCIOColorspace / Colorspace Class function
    def colorspace_class(self):
        """
        Set up the UI for OCIOColorSpace and Colorspace nodes.
        """

        knob_map = {
            'ociocolorspace': {
                'in_knob': 'in_colorspace',
                'out_knob': 'out_colorspace',
            },
            'colorspace': {
                'in_knob': 'colorspace_in',
                'out_knob': 'colorspace_out',
            }
        }

        self.LabelCraftUI.grp_Colorspaces.setVisible(True)
        self.LabelCraftUI.grp_Colorspaces.setTitle('{} knobs'.format(self.node.name()))

        self.in_knob_name = knob_map[self.current_node_class]['in_knob']
        self.out_knob_name = knob_map[self.current_node_class]['out_knob']

        colorspace_options = self.node[self.in_knob_name].values()
        in_knob_state = str(self.node[self.in_knob_name].value())
        out_knob_state = str(self.node[self.out_knob_name].value())

        self.in_button =  self.LabelCraftUI.btn_colorspace_in
        self.in_button.setText(in_knob_state)
        self._in_menu = ColorspaceCascadingMenu(self.in_button, self.in_knob_name)
        self._in_menu.set_entries(colorspace_options)
        self._in_menu.itemSelected.connect(self.change_colorspace_knob)

        self.out_button = self.LabelCraftUI.btn_colorspace_out
        self.out_button.setText(out_knob_state)
        self._out_menu = ColorspaceCascadingMenu(self.out_button, self.out_knob_name)
        self._out_menu.set_entries(colorspace_options)
        self._out_menu.itemSelected.connect(self.change_colorspace_knob)

        self.LabelCraftUI.btn_ColorspaceSwap.clicked.connect(self.swap_colorspaces)

    def change_colorspace_knob(self, selected_item, btn_name):
        """
        Change the colorspace of the Read node.
        """
        button_label = selected_item

        _parts = selected_item.split('/')
        if _parts:
            button_label = _parts[-1]

        button = self.LabelCraftUI.findChild(QtWidgets.QPushButton, btn_name)
        if button:
            button.setText(button_label)
        self.node[btn_name].setValue(str(selected_item))

    def swap_colorspaces(self):
        """
        Swap the input and output colorspaces.
        """
        in_knob_state = str(self.node[self.in_knob_name].value())
        out_knob_state = str(self.node[self.out_knob_name].value())

        self.node[self.in_knob_name].setValue(out_knob_state)
        self.node[self.out_knob_name].setValue(in_knob_state)

        self.in_button.setText(str(out_knob_state))
        self.out_button.setText(str(in_knob_state))

    # Dot/ Backdrop/ StickyNote Class function
    def info_class(self):
        """
        Set up the UI for Dot, Backdrop, and StickyNote nodes.
        """
        self.LabelCraftUI.grp_Info.setVisible(True)
        self.LabelCraftUI.grp_Info.setTitle('{} knobs'.format(self.node.name()))

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
        self.LabelCraftUI.grp_Scanline.setTitle('{} knobs'.format(self.node.name()))

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

    # Frames/ Times Class functions
    def frames_class(self):
        """
        Set up the UI for frame-related nodes.
        """

        knobs_map = {
            'framehold': ['first_frame', 'increment', 'set_to_current'],
            'framerange': ['first_frame', 'last_frame', 'reset'],
            'frameblend': ['numframes', None, None],
            'timeoffset': ['time_offset', None, None],
        }

        self.LabelCraftUI.grp_frame.setVisible(True)
        self.LabelCraftUI.grp_Tracker.setTitle('{} knobs'.format(self.node.name()))
        self.LabelCraftUI.lbl_last_frame.hide()
        self.LabelCraftUI.spn_last_frame.hide()
        self.LabelCraftUI.btn_frames.hide()

        self.LabelCraftUI.spn_first_frame.setRange(-10000, 10000)
        self.LabelCraftUI.spn_last_frame.setRange(-10000, 10000)

        self.first_knob = knobs_map[self.current_node_class][0]
        self.first_value = self.node[self.first_knob].value()

        self.LabelCraftUI.lbl_first_frame.setText(self.first_knob.replace('_', ' '))
        self.LabelCraftUI.spn_first_frame.setValue(self.first_value)

        self.last_knob = knobs_map.get(self.current_node_class, [None, None, None])[1]
        self.btn_custom = knobs_map.get(self.current_node_class, [None, None, None])[2]

        if self.last_knob:
            self.LabelCraftUI.lbl_last_frame.show()
            self.LabelCraftUI.spn_last_frame.show()
            self.last_value = self.node[self.last_knob].value()
            self.LabelCraftUI.lbl_last_frame.setText(self.last_knob.replace('_', ' '))
            self.LabelCraftUI.spn_last_frame.setValue(self.last_value)

        if self.btn_custom:
            self.LabelCraftUI.btn_frames.show()
            self.LabelCraftUI.btn_frames.setText(self.btn_custom.replace('_', ' '))

        self.LabelCraftUI.spn_first_frame.setObjectName(self.first_knob)
        self.LabelCraftUI.spn_last_frame.setObjectName(self.last_knob)

        self.LabelCraftUI.spn_first_frame.valueChanged.connect(lambda: self.update_frame_knobs(self.first_knob))
        self.LabelCraftUI.spn_last_frame.valueChanged.connect(lambda: self.update_frame_knobs(self.last_knob))
        self.LabelCraftUI.btn_frames.clicked.connect(lambda: self.pressed_frame_button(self.btn_custom))

    def update_frame_knobs(self, knob_name):
        """
        Update the value of the specified frame-related knob.
        """

        widget = self.LabelCraftUI.findChild(QtWidgets.QSpinBox, knob_name)
        if widget:
            self.node[knob_name].setValue(int(widget.value()))

    def pressed_frame_button(self, operation):
        """
        Perform custom operations for frame-related nodes.

        Args:
            operation (str): The operation to perform.
        """
        if operation == 'set_to_current':
            self.node['first_frame'].setValue(nuke.frame())
            self.LabelCraftUI.spn_first_frame.setValue(nuke.frame())

        elif operation == 'reset':
            self.node[self.btn_custom].execute()

    # ================ #
    # UI related functions
    @staticmethod
    def smart_position_window(dialog):
        """Position dialog under the cursor"""
        cursor_pos = QtGui.QCursor.pos()

        app = QtWidgets.QApplication.instance()

        if hasattr(app, 'desktop'):
            desktop = app.desktop()
            screen_num = desktop.screenNumber(cursor_pos)
            screen_rect = desktop.availableGeometry(screen_num)
        else:
            for screen in app.screens():
                if screen.geometry().contains(cursor_pos):
                    screen_rect = screen.availableGeometry()
                    break
            else:
                screen_rect = app.primaryScreen().availableGeometry()

        dialog_width = dialog.width()
        dialog_height = dialog.height()

        if dialog_height > screen_rect.height() * 0.7:
            y = cursor_pos.y() - dialog_height - 10
        else:
            y = cursor_pos.y() + 20
            if y + dialog_height > screen_rect.bottom():
                y = cursor_pos.y() - dialog_height - 10

        # Center horizontally
        x = cursor_pos.x() - (dialog_width // 2)

        # Ensure it stays on screen
        x = max(screen_rect.left(), min(x, screen_rect.right() - dialog_width))
        y = max(screen_rect.top(), min(y, screen_rect.bottom() - dialog_height))

        dialog.move(int(x), int(y))

    # Main Function that calls the corresponding Class
    def edit_node(self):
        """
        Edit the selected node by setting up the appropriate UI components based on the node class.
        """
        self.node = get_selection()

        if not self.node:
            return

        self.current_node_class = self.node.Class().lower()

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

        elif self.node.Class() in ('OCIOColorSpace', 'Colorspace'):
            self.current_node_class = self.node.Class().lower()
            self.colorspace_class()

        elif self.node.Class() in ('Dissolve', 'Switch'):
            self.current_node_class = self.node.Class().lower()
            self.switch_class()

        elif self.node.Class() in ('ScanlineRender', 'ScanlineRender2'):
            self.current_node_class = self.node.Class().lower()
            self.scanline_class()

        elif self.node.Class() in ('TimeOffset', 'FrameHold', 'FrameRange', 'FrameBlend'):
            self.current_node_class = self.node.Class().lower()
            self.frames_class()

        ### Final UI adjustments ###
        # Resize to its contents, and re-position under the mouse
        self.LabelCraftUI.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Popup
        )

        # self.LabelCraftUI.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |
        #                                  QtCore.Qt.Window)

        self.LabelCraftUI.adjustSize()
        self.smart_position_window(self.LabelCraftUI)

        # Set Focus to the Label Box
        self.LabelCraftUI.edt_NodeLabel.setFocusPolicy(Qt.StrongFocus)
        self.LabelCraftUI.edt_NodeLabel.setFocus()

        self.LabelCraftUI.show()


def edit_label():
    """
    Initialize and run the LabelCraft tool.
    """
    run_labelcraft = LabelCraft()
    run_labelcraft.edit_node()


if __name__ == '__main__':
    edit_label()
