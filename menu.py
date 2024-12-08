import LabelCraft
import nuke

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
