standard_shuffle = 'Shuffle'  # 'Shuffle2'  ## 'nuke version'

label_presets = {"tracker": ["[value transform] : [value reference_frame]",
                             "[value reference_frame]",
                             "[value transform]",
                             "[value filter]"],
                 "read": ["[value colorspace]"],
                 "shuffle": ["[value in]",
                             "[value out]"],
                 "shuffle2": ["[value in1]",
                              "[value in2]",
                              "[value out1]",
                              "[value out2]"],
                 "roto": ["[value reference_frame]",
                          "[value output]"],
                 "switch": ["[value which]",
                            "[if {[value which]==0} {return 'Original Plate'} {return 'Pre Render Plate'}]",
                            "[if {[value which]==0} {return 'BG Render'} {return 'GUI'}]"],
                 "dissolve": ["[value which]"],
                 "framehold": ["[value first_frame]"],
                 "log": ["[value operation]"],
                 "merge": ["[value operation]",
                           "[value bbox]",
                           "[value mix]",
                           "[knob tile_color [ expr { [value disable] ? 4278190335 : 0 } ] ]"],
                 "channelmerge": ["[value operation]",
                                  "[value bbox]",
                                  "[value mix]"],
                 "keymix": ["[value operation]",
                            "[value bbox]",
                            "[value mix]"],
                 "framerange": ["[value first_frame] - [value last_frame]"],
                 "blur": ["[value size]"],
                 "transform": ["[value translate]",
                               "[value rotate]",
                               "[value scale]",
                               "[value filter]"]}


icon_selection = ['none', '2D', '3D', 'Axis', 'Add', 'Anaglyph', 'Assert',
                  'Bezier', 'Camera',
                  'Card', 'ChannelMerge', 'Color', 'ColorAdd', 'ColorBars', 'ColorCorrect', 'ColorLookup',
                  'ClipTest', 'ColorAdd', 'ColorSpace', 'CornerPin', 'Crop', 'Cube', 'Color', 'CheckerBoard',
                  'ColorBars', 'ColorCorrect', 'Dot', 'DegrainSimple',
                  'EnvironMaps', 'Exposure', 'Expression',
                  'HueShift', 'FloodFill', 'Input', 'ImageModeler',
                  'Keyer', 'Keymix', 'Light', 'MarkerRemoval', 'Merge', 'Modify',
                  'NukeXApp48', 'Output', 'OCIO',
                  'Paint', 'Particles', 'Position', 'PostageStamp', 'Primatte',
                  'Read', 'Render', 'RotoPaint',
                  'Saturation', 'Shuffle', 'Sphere', 'Sparkles', 'SpotLight', 'Scene', 'Switch',
                  'TimeClip', 'Tracker', 'Viewer', 'Write']


dissolve_expressions = {'liner': 'clamp( ( frame - value_A ) / ( value_B - value_A))',
                        'easy in-out': '(sin(clamp( ( ( frame - value_A ) * pi ) / ( value_B - value_A ) - pi / 2 , - pi / 2, pi / 2 ) ) + 1) / 2',
                        'easy in': 'sin(clamp( ( ( frame - value_A ) * pi ) / ( ( value_B - value_A ) * 2 ) - pi / 2, -pi / 2,0 ) ) + 1',
                        'easy out': 'sin(clamp( ( ( frame - ( value_A * 2 - value_B ) ) * pi ) / ( ( value_B - value_A ) * 2 ) - pi / 2,0, pi / 2) )'}


switch_expressions = {'input 1 on GUI': '$gui',
                      'input 0 on GUI': '!$gui',
                      'input 1 at frame': 'frame == value_A',
                      'input 1 after frame': 'frame > value_A',
                      'input 1 before frame': 'frame < value_A',
                      'input 1 inbetween range': 'inrange(frame, value_A, value_B)'}

which_expressions = {
    'switch': {'input 1 on GUI': '$gui',
               'input 0 on GUI': '!$gui',
               'input 1 at frame': 'frame == value_A',
               'input 1 after frame': 'frame > value_A',
               'input 1 before frame': 'frame < value_A',
               'input 1 inbetween range': 'inrange(frame, value_A, value_B)'},
    'dissolve': {'liner': 'clamp( ( frame - value_A ) / ( value_B - value_A))',
                 'easy in-out': '(sin(clamp( ( ( frame - value_A ) * pi ) / ( value_B - value_A ) - pi / 2 ,'
                                '- pi / 2, pi / 2 ) ) + 1) / 2',
                 'easy in': 'sin(clamp( ( ( frame - value_A ) * pi ) / ( ( value_B - value_A ) * 2 ) - pi / 2,'
                            '-pi / 2,0 ) ) + 1',
                 'easy out': 'sin(clamp( ( ( frame - ( value_A * 2 - value_B ) ) * pi ) /'
                             '( ( value_B - value_A ) * 2 ) - pi / 2,0, pi / 2) )'}
}