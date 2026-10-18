# SPDX-License-Identifier: GPL-2.0-or-later
"""Opt-in RX 580 compatibility preset; based on the AMD preset plus image barrier merging."""
from presets_amd import AMD

RX580 = {
    'id': 'rx580',
    'exported': '2026-10-18',
    'names': {'en': 'RX 580 COMPATIBILITY (EXPERIMENTAL)', 'pt': 'COMPATIBILIDADE RX 580 (EXPERIMENTAL)'},
    'what': {
        'en': 'AMD recommended settings plus experimental image-subresource barrier merging. One RX 580 user '
              'reported improved compatibility; this is unconfirmed and may affect other GPUs.',
        'pt': 'Configuração recomendada para AMD mais junção experimental de barreiras de sub-recursos de imagem. '
              'Um usuário de RX 580 relatou melhora de compatibilidade; não foi confirmado e pode afetar outras GPUs.',
    },
    'settings': dict(AMD['settings']),
    'items': dict(AMD['items'], TLG_BARRIER_MERGE='1'),
}
