import smartLabel

toolbar = nuke.toolbar("Nodes")
mainMenu = toolbar.addMenu("SmartLabel 2.0")
mainMenu.addCommand('SmartLabel 2.0', 'smartLabel.run()', 'shift+q', icon = 'Text.png')
