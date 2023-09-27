import SmartLabel
import setLabel

toolbar = nuke.toolbar("Nodes")
mainMenu = toolbar.addMenu("SmartLabel 2.0")
mainMenu.addCommand('SmartLabel 2.0', 'SmartLabel.run()', 'shift+q', icon = 'Text.png')
mainMenu.addCommand('Set Label 2.0', 'setLabel.run()', 'ctrl+q', icon = 'Text.png')
