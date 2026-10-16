"""Small tables and rules of the game's engine that decide register and sharp values.

Every entry says where it comes from:
    EBOOT     read in the 1.07 executable (function named in the comment); enums only
    INFERRED  inferred from a development capture (jobs_eval.py infer); each one is a
              reverse-engineering task until the eboot confirms it
The INFERRED tables are not in this file: `jobs_eval.py infer` writes them to a JSON file of
enums only (formats, strides, masks, api slots, pass ids), and `jobs.py --tables` reads it.
Nothing here holds game bytes, hashes or shader numbers.
"""
from __future__ import annotations

import json
from typing import Optional, Tuple

EBOOT, INFERRED = "eboot", "inferred"

# --- EBOOT: DB_SHADER_CONTROL rewrite when an effect is loaded (FUN_014468e0, REVISAO B4) ---
SOURCE_DB_SHADER_CONTROL = EBOOT


def db_shader_control(v: int) -> int:
    if v & 0x40:
        v = 0x60
    if v & 1:
        v &= ~0x30
    if v & 0x900:
        v = 0x920
    return v


# --- EBOOT: pass stage codes (pairs +0x88/+0x98: {stage code, descriptor}); DAT_01987c80 maps
# them to Gnm stages, 0 = VS and 3 = PS are the only ones the index has ---
SOURCE_STAGE_CODES = EBOOT
STAGE_CODE = {0: "VS", 3: "PS"}

# --- EBOOT: material textures (FUN_01447190, FUN_01448640, FUN_0144a250; PLAN F3/F4, B7) ---
#   material texture i -> descriptor b = effect.matmap[i] (+0xE0); every pass pair {stage, b}
#   of +0x98 binds it at api slot tex_desc[b] + 0xB (descriptors of 0x10 bytes at +0xD0);
#   the T# is the texture object's (+0x18), or a default one when the material has none.
SOURCE_MATERIAL_TEXTURES = EBOOT
TEX_DESC_SIZE, TEX_DESC_TYPE, TEX_DESC_API, TEX_DESC_SWAP = 0x10, 0x8, 0xB, 0xC
MAT_TEX_ENTRY = 0x30
#   samplers: pass pairs +0x88 {stage, d} -> smp_desc[d] (0x20 bytes at +0xC0): +8 api slot,
#   +0xC the S# (FUN_01447fa0)
SOURCE_EFFECT_SAMPLERS = EBOOT
SMP_DESC_SIZE, SMP_DESC_API, SMP_DESC_SHARP = 0x20, 0x8, 0xC

# --- EBOOT: sRGB swap of a material texture (FUN_0144a130, REVISAO B3) ---
# when descriptor +0xC == 0, fmtword[23:20] == 1 and fmtword[15:8] is one of these codes, the
# T# gets this data format, number format sRGB and dst_sel xyzw
SOURCE_SRGB_SWAP = EBOOT
SRGB_SWAP_DFMT = {0: 10, 6: 35, 7: 36, 8: 37, 13: 41}   # 8_8_8_8, BC1, BC2, BC3, BC7


def srgb_swap(words: list, fmtword: int, desc_swap: int) -> list:
    """The T# words a material texture is bound with (FUN_0144a250 -> FUN_0144a130)."""
    w = list(words)
    if desc_swap != 0 or (fmtword >> 20) & 0xF != 1:
        return w
    code = (fmtword >> 8) & 0xFF
    df = SRGB_SWAP_DFMT.get(code)
    if df is None:
        return w
    w[1] = (w[1] & 0xC00FFFFF) | df << 20 | 9 << 26
    w[3] = (w[3] & 0xFFFFF000) | 4 | 5 << 3 | 6 << 6 | 7 << 9
    return w


# --- EBOOT/measured: canonical constant buffer V# (PLAN F5: stride 16, dword3 0x20077FAC) ---
SOURCE_CB = EBOOT
CB_DWORD3 = 0x20077FAC
CB_STRIDE = 16

# --- INFERRED (F5, measured on the reference cache, not yet read in the eboot): the image type
# of an engine texture from its descriptor byte +8 ---
SOURCE_DESC_TYPE = INFERRED
DESC_TYPE_TO_IMAGE = {2: 9, 3: 10, 4: 11, 7: 11, 5: 12, 6: 13}

# --- INFERRED: what a material slot gets when the material has no texture (DAT_08d4c348 and
# DAT_08d4c358 are runtime objects; their format is unknown offline) ---
SOURCE_DEFAULT_TEXTURE = INFERRED
DEFAULT_TEXTURE = (9, 10, 0, (4, 5, 6, 7))    # 2D, 8_8_8_8, unorm, xyzw


# --- compute V# per InputUsageSlot (re_compute report, 16/10: measured on two caches, 1,483
# compute .meta files of 745 programs; the strides with an all.c line are EBOOT) ---
#   (usageType, apiSlot) -> stride: a number, "def" (u32 at +0x88 of the particle definition
#   that holds the kernel, FUN_013f09a0 initAsRegularBuffer) or "code" (from the accesses)
SOURCE_COMPUTE_SLOTS = {"4,1": EBOOT, "4,2": EBOOT, "4,5": EBOOT, "4,6": EBOOT, "2,*": EBOOT,
                        "other": INFERRED}
COMPUTE_SLOTS = {(4, 1): "def", (4, 0): 1, (4, 2): 96, (4, 3): 8, (4, 4): "code", (4, 5): 176,
                 (4, 6): 80, (0, 3): 16, (0, 4): 4, (0, 5): 16, (0, 6): 4, (0, 7): 48, (0, 8): 4,
                 (0, 10): 32, (0, 11): 48}
CS_RW_DWORD3, CS_RO_DWORD3 = 0x18027204, 0x20027204     # mtype 3 (written) / 4 (read only)
# the "previous state" V# in s[0:3] (no InputUsageSlot) is null on the first frame of a particle
# effect (FUN_013f09a0, all.c l.887323-887326): one record with it null and one with it bound
SOURCE_CS_PREVIOUS_STATE = EBOOT
# (a synthetic unbound V#: num_records 0 is all the signature and the port look at)
CS_NULL_VSHARP = [0, 0, 0, 0x20027204]
# definition: def+0x90 and def+0x98 point at the two kernel shader objects, whose Gnm header
# pointer is at +0x30 (FUN_013f2bd0); the state stride is the u32 at def+0x88
PARTICLE_KERNELS, PARTICLE_STRIDE, SHADER_OBJ_HDR = (0x90, 0x98), 0x88, 0x30


class Tables:
    """The INFERRED tables written by `jobs_eval.py infer` (JSON of enums only)."""

    def __init__(self, data: Optional[dict] = None):
        data = data or {}
        self.source = data.get("source", INFERRED)
        # pass id -> [profile]: {"state": {"off", "cb": {cb: [fmt, ntype, swap, blend, mask,
        # frag_log2]}, "depth": [z, stencil, samples_log2, clamp], "raster": [prim, poly mode,
        # provoking, zclip, clip space, rop3], "vs": [clip planes, clip space, clip disable,
        # step rate 0, step rate 1, emulated prim]}, "VS": {key: witness}, "PS": {key: witness}}
        # with key "usage/api/dwords" (jobs.witness_of); one profile per captured draw
        self.engine = {int(k): v for k, v in data.get("engine", {}).items()}
        # [{key: witness}] of the compute dispatches
        self.compute = data.get("compute", [])
        # key -> witness: the most common value of each slot key over all profiles
        self.fallback = data.get("fallback", {})

    @classmethod
    def load(cls, path) -> "Tables":
        with open(path) as f:
            return cls(json.load(f))

    def dump(self) -> dict:
        return {"source": self.source, "engine": self.engine,
                "compute": self.compute, "fallback": self.fallback}


def slot_key(usage: int, api, dwords: int) -> str:
    return f"{usage}/{api}/{dwords}"


def parse_key(key: str) -> Tuple:
    a, b, c = key.split("/")
    return (a if a == "implicit" else int(a), int(b), int(c))
