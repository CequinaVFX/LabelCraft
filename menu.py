import main
import nuke

print('Label Craft Original ', main.__version__)

SHORTCUT = 'shift+q'
ICON = 'LabelCraft.png'

toolbar = nuke.toolbar("Nodes")
mainMenu = toolbar.addMenu("CQN Tools")
mainMenu.addCommand('LabelCraft', 'main.edit_label()', SHORTCUT, icon=ICON, shortcutContext=dagContext)
