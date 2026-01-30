import LabelCraft
import nuke

nuke.tprint('\n\t', __title__, __version__, '\n')

# Define the shortcut for the tool
# The shortcut is defined as a string, where the key is separated by a '+'
# The key can be any key on the keyboard, and the modifier keys are 'shift', 'ctrl', 'alt', 'meta'
# The shortcut is not case sensitive
# Examples: 'q', 'shift+q', 'ctrl+shift+q', 'f4'
SHORTCUT = 'shift+q'


ICON = 'LabelCraft.png'
dagContext = 2

toolbar = nuke.toolbar("Nodes")
mainMenu = toolbar.addMenu("CQN Tools")
mainMenu.addCommand('LabelCraft',
                    'LabelCraft.edit_label()',
                    SHORTCUT,
                    icon=ICON,
                    shortcutContext=dagContext)
