# SPDX-License-Identifier: GPL-2.0-or-later
"""The "currently recommended" preset: the settings the maintainer plays with (2026-10-16).

A full preset: besides the switches the four plain presets set (qt/gfxlogic.py), it also sets GPU
accuracy, read-ahead, write merge and the draw-distance values. The plain presets leave those alone.
Left out on purpose (they depend on the machine): the VRAM budget, window mode, languages, and the
AMD workarounds (BLOCK1D, BC_TINY, NO_MSAA), which stay on "Automatic".
"""

CURRENT = {
    'id': 'current',
    'exported': '2026-10-16',
    'names': {'en': 'CURRENTLY RECOMMENDED', 'pt': 'RECOMENDADA ATUALMENTE'},
    'what': {
        'en': 'The maintainer\'s own setup: exact GPU reads (Precise), read-ahead off, FSR 1 on, shorter draw '
              'distance with sharper textures, and the driver pipeline cache. Changes GPU accuracy too.',
        'pt': 'A configuração do próprio autor: leituras exatas da GPU (Preciso), leitura adiantada desligada, '
              'FSR 1 ligado, alcance de visão menor com texturas mais nítidas e o cache de pipelines do driver. '
              'Também muda a precisão da GPU.',
    },
    # launcher settings (settings.json): keys the plain presets do not touch, plus VSync
    'settings': {'vsync': True, 'gpu_readbacks': '2', 'eager_readback': False, 'write_merge': True},
    # table items (backports_table.py ids), values as stored strings; a value equal to the default is "off the list"
    'items': {
        'menu:fsr1': '1',
        'menu:lod_scale': '0.6',
        'menu:region_lod': '0',
        'menu:region_fade': '0.8',
        'menu:far_clip': '1418000',
        'menu:mip_lod_bias': '1.25',
        'BP07': '1',
        'BP08': '1',
    },
    # in the export for reference, never applied
    'not_applied': {
        'vram_budget_mb': 3500, 'display_mode': 'Windowed', 'block1d': 'auto (1 on this PC)',
        'bc_tiny': 'auto (1 on this PC)', 'no_msaa': 'auto (1 on this PC)', 'engine_fps': 120,
    },
}
