import main
import nuke

SHORTCUT = 'shift+q'
ICON = 'LabelCraft.png'

toolbar = nuke.toolbar("Nodes")
mainMenu = toolbar.addMenu("CQN Tools")
mainMenu.addCommand('LabelCraft', 'main.get_selection()', SHORTCUT, icon=ICON)
