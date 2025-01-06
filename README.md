# LabelCraft

## Overview
LabelCraft is a comprehensive labeling tool designed for Foundry's Nuke software. It provides an intuitive interface for customizing node labels, icons, colors, and attributes with ease. Whether you're working with trackers, merge nodes, or sticky notes, LabelCraft streamlines your workflow.

## Features
- Label customization with HTML formatting (alignment, bold, italic, icons) to Backdrops and StickyNotes.
- Dynamic UI adapting to different node types.
- Easy manipulation of node-specific attributes (e.g., `operation`, `bbox`, `reference frame`, `log2lin`).
- Shuffle layers and channels with a single click.
- Node-specific presets for quick label application.
- Supports Python 2.7 and 3.7, ensuring compatibility across Nuke versions.

## Requirements
- **Nuke:** Version 11 or later.
- **Operating System:** Windows, macOS, or Linux.

## Installation
1. **Download the repository** from https://github.com/CequinaVFX/LabelCraft.
2. **OR Clone the repository**:
   ```bash
   git clone https://github.com/CequinaVFX/LabelCraft.git
   ```
3. Unzip and rename the folder to `LabelCraft`
4. Copy the folder to .nuke standard folder.
5. Add these line to init.py (`create a new one if it doesn't exist`):
   ```python
   import nuke 
   nuke.pluginAddPath('./LabelCraft')
   ```
Where to find the .nuke folder: https://learn.foundry.com/nuke/12.2/content/user_guide/configuring_nuke/finding_nuke_home.html

## License
This project is licensed under the MIT License.

## Support
For questions or suggestions, contact:
- **Author:** Luciano Cequinel
- **Contact:** www.cequinavfx.com
- **Tool's blog:** www.cequinavfx.com/post/label-craft
