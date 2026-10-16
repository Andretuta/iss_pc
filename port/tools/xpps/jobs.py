"""Job builder v1: precompile records (vk_precompile.h) from the index of the player's own files.

    python -m xpps.jobs <index.sqlite> <tables.json> <out.jobs> [--game <art/cache>]
                        [--max-state N] [--max-material N] [--max-compute N] [--no-compute]

For every pass (VS + PS pair of an effect, with its render slot = pass id) and every compute
shader of the index it writes the records the precompiler compiles before the game starts:
    registers  the Gnm header of each shader (RSRC1/2, export formats, PS input enables, ...),
               DB_SHADER_CONTROL through the load rule (engine_tables, EBOOT), SPI_PS_INPUT_CNTL
               from the VS export and PS input semantics, and the render target / depth /
               raster state of the pass id from the INFERRED state profiles
    sharps     at flat[startRegister] of every InputUsageSlot: material T# by the effect and
               material instance (EBOOT rules, with the sRGB swap), effect samplers, canonical
               constant buffers, and the rest (engine buffers and textures) from the INFERRED
               profiles of the same pass id
    vertex     the fetch shader of the pass and, per attribute it loads, the V# of a mesh that
               uses the effect
    code       read from the .xpps files (never stored anywhere else)
The output stays on the player's machine. Progress lines `PROGRESS jobs <n> <total>` go to stdout.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import mmap
import os
import sqlite3
import struct
import sys
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

from . import engine_tables as ET
from . import gcn_mem
from . import jobfile
from . import kcap, knli
from . import signature as S

U64 = (1 << 64) - 1
PASS_SIZE = 0xB8
BINARY_INFO_PAD = 4          # sizeof(AmdGpu::BinaryInfo) 32 - the 28 bytes of the footer
SMRD_ENCODING, S_LOAD_DWORDX4 = 0b11000, 2


# --- sharps: witnesses (enum fields only) <-> words ---------------------------------------
def witness_of(usage: int, words) -> list:
    """The enum fields of a sharp (what the tables store). words: 4 or 8 u32."""
    if usage == S.USAGE_SAMPLER:
        return ["S", S.bits(words[0], 15, 1), S.bits(words[0], 20, 1)]
    if len(words) == 8:
        f = S.image_fields(words)
        return ["I", int(f["base"] != 0), f["type"], f["dfmt"], f["nfmt"], list(f["dst_sel"])]
    f = S.buffer_fields(words)
    return ["B", int(f["num_records"] != 0), f["stride"], f["swizzle_enable"], f["index_stride"],
            f["element_size"], f["dfmt"], f["nfmt"], list(f["dst_sel"]), f["mtype"], f["add_tid"]]


def words_of(w) -> List[int]:
    """Synthetic sharp words with the enum fields of a witness (addresses are placeholders)."""
    kind = w[0]
    if kind == "S":
        return [w[1] << 15 | w[2] << 20, 0, 0, 0]
    if kind == "I":
        bound, typ, df, nf, sel = w[1], w[2], w[3], w[4], w[5]
        d3 = sel[0] | sel[1] << 3 | sel[2] << 6 | sel[3] << 9 | typ << 28
        return [1 if bound else 0, df << 20 | nf << 26, 0, d3, 0, 0, 0, 0]
    bound, stride, swz, ist, esz, df, nf, sel, mtype, tid = w[1:11]
    d1 = stride << 16 | swz << 31
    d3 = (sel[0] | sel[1] << 3 | sel[2] << 6 | sel[3] << 9 | nf << 12 | df << 15 | esz << 19 |
          ist << 21 | tid << 23 | mtype << 27)
    return [0x100 if bound else 0, d1, 1 if bound else 0, d3]


CB_WORDS = [0x100, ET.CB_STRIDE << 16, 1, ET.CB_DWORD3]


def proj_witness(usage: int, w) -> tuple:
    """Signature projection of a witness (same as signature.proj_slot of its words)."""
    words = words_of(w)
    if w[0] == "S":
        return S.proj_sampler(words)
    if w[0] == "I":
        return S.proj_image(words, usage == S.USAGE_RW)
    return S.proj_buffer(words, usage == S.USAGE_CB)


def slot_list(h: S.Header):
    return [tuple(h.slots[i:i + 4]) for i in range(0, len(h.slots) - len(h.slots) % 4, 4)]


def sharp_slots(h: S.Header):
    """(key, usage, api, start, dwords) of the slots that hold a sharp, then the implicit quads."""
    out, covered = [], set()
    for s in slot_list(h):
        n = S.slot_dwords(s)
        covered.update(range(s[2], s[2] + n))
        if s[0] in S.SHARP_USAGES:
            out.append((ET.slot_key(s[0], s[1], n), s[0], s[1], s[2], n))
    nud = S.bits(h.words["RSRC2"], 1, 5)
    for q in range(0, min(nud, 16) - 3, 4):
        if not covered.intersection(range(q, q + 4)):
            out.append((ET.slot_key("implicit", q, 4), S.USAGE_RESOURCE, q, q, 4))
    return out


def vs_input_semantics(vh: S.Header):
    """{semantic, vgpr, sizeInElements, reserved} of each vertex input (Gnm VS header)."""
    n = vh.regs_raw[0x14]
    return [tuple(vh.semantics[4 * i:4 * i + 4]) for i in range(n) if 4 * i + 4 <= len(vh.semantics)]


def fetch_loads(code: bytes) -> List[Tuple[int, int]]:
    """(sgpr base, dword offset) of every s_load_dwordx4 of a fetch shader (one per attribute)."""
    out = []
    for i in range(0, len(code) - 3, 4):
        (w,) = struct.unpack_from("<I", code, i)
        if w >> 27 == SMRD_ENCODING and (w >> 22) & 31 == S_LOAD_DWORDX4 and (w >> 8) & 1:
            out.append((((w >> 9) & 63) * 2, w & 0xFF))
    return out


# --- registers ----------------------------------------------------------------------------
def header_regs(vh: S.Header, ph: S.Header) -> Dict[int, int]:
    regs = {}
    for name, idx in S.VS_HDR_REG.items():
        regs[idx] = vh.words[name]
    for name, idx in S.PS_HDR_REG.items():
        regs[idx] = ph.words[name]
    regs[S.DB_SHADER_CONTROL] = ET.db_shader_control(ph.words["DB_SHADER_CONTROL"])
    for i, v in enumerate(ps_input_cntl(vh, ph)):
        regs[S.SPI_PS_INPUT_CNTL_0 + i] = v
    return regs


def ps_input_cntl(vh: S.Header, ph: S.Header) -> List[int]:
    """SPI_PS_INPUT_CNTL_i from the semantics (Gnm's PS usage table; 614/614 on the capture):
    the VS export with the same semantic gives the offset, else 0x20 | default value; flat
    shading (bit 10) is kept and a custom input (bit 12) sets 0x20."""
    exports = {e & 0xFF: (e >> 8) & 0x1F for e in vh.vs_exports()}
    out = []
    for p in ph.ps_inputs():
        v = exports.get(p & 0xFF)
        v = 0x20 | ((p >> 8) & 3) << 8 if v is None else v
        if p & 0x400:
            v |= 0x400
        if p & 0x1000:
            v |= 0x20
        out.append(v)
    return out


def state_regs(st: dict) -> Dict[int, int]:
    """Registers that give a state profile back through signature.color_targets/effective_depth/
    raster/vs_runtime."""
    regs = {}
    raster = st["raster"]
    prim, poly_mode, provoking, zclip, clip_space, rop3 = raster
    if st.get("off"):
        regs[S.CB_COLOR_CONTROL] = rop3 << 16
    else:
        regs[S.CB_COLOR_CONTROL] = 1 << 4 | rop3 << 16
    tmask = 0
    for cb, (fmt, ntype, swap, blend, mask, frag) in st["cb"].items():
        cb = int(cb)
        base = S.CB_COLOR0_BASE + S.CB_COLOR_STRIDE * cb
        regs[base] = 1
        regs[base + S.CB_INFO] = fmt << 2 | ntype << 8 | swap << 11
        regs[base + S.CB_ATTRIB] = frag << 15
        if blend:
            regs[S.CB_BLEND0_CONTROL + cb] = blend
        tmask |= mask << 4 * cb
    regs[S.CB_TARGET_MASK] = tmask
    z, s, samples, clamp = st["depth"]
    ctl = 0
    if z:
        regs[S.DB_Z_INFO] = z | samples << 2
        regs[S.DB_Z_READ_BASE] = regs[S.DB_Z_WRITE_BASE] = 1
        ctl |= 2 | 4 | 3 << 4
    if s:
        regs[S.DB_STENCIL_INFO] = s
        regs[S.DB_STENCIL_READ_BASE] = regs[S.DB_STENCIL_WRITE_BASE] = 1
        ctl |= 1 | 1 << 8
        if not z:
            regs[S.DB_Z_INFO] = samples << 2
    regs[S.DB_DEPTH_CONTROL] = ctl
    regs[S.DB_RENDER_OVERRIDE] = (1 - clamp) << 16
    vs = st["vs"]          # clip plane mask, clip space, clip disable, step 0, step 1, tess
    clip = vs[0] | (vs[2] and prim != 0x11) << 16 | clip_space << 19
    if not zclip:
        clip |= 3 << 26
    regs[S.PA_CL_CLIP_CNTL] = clip
    poly = provoking << 19
    if poly_mode != 2:
        poly |= 1 << 3 | poly_mode << 5 | poly_mode << 8
    regs[S.PA_SU_SC_MODE_CNTL] = poly
    regs[S.VGT_PRIMITIVE_TYPE] = prim
    regs[S.VGT_INSTANCE_STEP_RATE_0], regs[S.VGT_INSTANCE_STEP_RATE_1] = vs[3], vs[4]
    return {k: v for k, v in regs.items() if v}


def state_of_signature(sig: dict, regs: dict) -> dict:
    """The state profile of a captured record (the inverse of state_regs)."""
    g = lambda i: regs.get(i, 0)
    cbs = {}
    for cb in range(S.NUM_CB):
        base = S.CB_COLOR0_BASE + S.CB_COLOR_STRIDE * cb
        info, attrib = g(base + S.CB_INFO), g(base + S.CB_ATTRIB)
        mask = S.bits(g(S.CB_TARGET_MASK), 4 * cb, 4)
        if not (g(base) and S.bits(info, 2, 5)) or not mask:
            continue
        blend = g(S.CB_BLEND0_CONTROL + cb)
        blend = blend if S.bits(blend, 30, 1) and not S.bits(info, 16, 1) else 0
        cbs[cb] = [S.bits(info, 2, 5), S.bits(info, 8, 3), S.bits(info, 11, 2), blend, mask,
                   S.bits(attrib, 15, 2)]
    vs = sig["vs_rt"]
    return {"off": sig["rt"] == ("off",), "cb": cbs, "depth": list(sig["depth"]),
            "raster": list(sig["raster"]), "vs": [vs[3], vs[4], vs[5], vs[6], vs[7], vs[8]]}


def project_state(st: dict, mask: int) -> tuple:
    if st.get("off"):
        cbs = ("off",)
    else:
        cbs = tuple((int(cb), tuple(v)) for cb, v in sorted(st["cb"].items(), key=lambda x: int(x[0]))
                    if mask >> int(cb) & 1)
    return (cbs, tuple(st["depth"]), tuple(st["raster"]), tuple(st["vs"]))


def restrict_state(st: dict, mask: int) -> dict:
    out = dict(st)
    out["cb"] = {int(cb): v for cb, v in st["cb"].items() if mask >> int(cb) & 1}
    return out


# --- the index ----------------------------------------------------------------------------
class Index:
    def __init__(self, path: str, game: Optional[str] = None):
        self.db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        meta = dict(self.db.execute("SELECT key, value FROM meta"))
        self.root = game or meta.get("root")
        self.files = {}
        for fid, p, kc in self.db.execute("SELECT id, path, kcap FROM files"):
            self.files[fid] = (p, json.loads(kc)["doff"] if kc else 0)
        self.headers = S.load_headers(self.db)
        self.code_at = {}
        for h, f, off, size in self.db.execute("SELECT hash, file, code_off, size FROM shaders"):
            self.code_at[h & U64] = (f, off, size)
        self._maps = {}

    def close(self):
        for f, m in self._maps.values():
            m.close()
            f.close()
        self._maps.clear()

    def read(self, fid: int, off: int, n: int) -> bytes:
        if fid not in self._maps:
            if len(self._maps) > 64:
                self.close()
            f = open(os.path.join(self.root, self.files[fid][0]), "rb")
            self._maps[fid] = (f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ))
        doff = self.files[fid][1]
        return bytes(self._maps[fid][1][doff + off:doff + off + n])

    def code(self, h: int) -> bytes:
        """The code up to the end of AmdGpu::BinaryInfo as the port reads it: the index size
        stops after the 28 bytes of the OrbShdr block, the C++ struct is 32 (padding)."""
        f, off, size = self.code_at[h]
        return self.read(f, off, size + BINARY_INFO_PAD)


def load_graphics_context(ix: Index, pairs: Optional[set] = None):
    """Passes grouped by (vs, ps, pass id, fetch), with their effect, material instances,
    textures and meshes."""
    db = ix.db
    eff_by_file = defaultdict(list)
    effects = {}
    for f, o, po, n, nmat, td, mm, sd in db.execute(
            "SELECT file, off, passes_off, n_passes, nmat_tex, tex_desc, matmap, smp_desc FROM effects"):
        effects[(f, o)] = (nmat or 0, td or b"", (mm or b"")[:nmat or 0], sd or b"")
        if po is not None:
            eff_by_file[f].append((po, n, o))
    for f in eff_by_file:
        eff_by_file[f].sort()
    groups = defaultdict(list)
    vs_effects = defaultdict(set)
    want_vs = {v for v, _p in pairs} if pairs is not None else None
    for (f, o, pid, vs, ps, fo, fs, tp, sp) in db.execute(
            "SELECT file, off, pass_id, vs, ps, fetch_off, fetch_size, tex_pairs, smp_pairs FROM passes"):
        vs, ps = vs & U64, ps & U64
        if want_vs is not None and vs not in want_vs:
            continue
        lst = eff_by_file.get(f, [])
        i = bisect.bisect_right(lst, (o, 1 << 62, 0)) - 1
        eff = None
        if i >= 0:
            po, n, eo = lst[i]
            if (o - po) % PASS_SIZE == 0 and (o - po) // PASS_SIZE < n:
                eff = (f, eo)
        if eff:
            vs_effects[vs].add(eff)
        if pairs is not None and (vs, ps) not in pairs:
            continue
        groups[(vs, ps, pid)].append((f, o, fo, fs, tp or b"", sp or b"", eff))
    needed = {e for lst in vs_effects.values() for e in lst}
    mats = defaultdict(list)
    for f, o, ef, eo, nt, tl in db.execute(
            "SELECT file, off, effect_file, effect_off, n_tex, tex_list FROM matinst WHERE effect_off IS NOT NULL"):
        if (ef, eo) in needed:
            mats[(ef, eo)].append((f, o, nt or 0, tl or b""))
    mat_keys = {(m[0], m[1]) for lst in mats.values() for m in lst}
    meshes = defaultdict(list)
    for f, mo, vsb in db.execute("SELECT file, matinst_off, vsharps FROM meshes"):
        if (f, mo) in mat_keys:
            meshes[(f, mo)].append(vsb or b"")
    tex = {}
    for h, ts, fw in db.execute("SELECT hash, tsharp, fmtword FROM textures ORDER BY file, off"):
        if h not in tex and ts:
            tex[h] = (struct.unpack("<8I", ts), fw or 0)
    return groups, effects, mats, meshes, tex, vs_effects


def material_bindings(effect, tex_pairs: bytes):
    """(stage, api) -> material index for the textures of a pass (FUN_01447190), and
    (stage, api) -> (type byte, swap flag) for every texture descriptor the pass binds."""
    nmat, td, mm, _sd = effect
    mat, desc = {}, {}
    for j in range(0, len(tex_pairs) - 1, 2):
        stage = ET.STAGE_CODE.get(tex_pairs[j])
        b = tex_pairs[j + 1]
        at = b * ET.TEX_DESC_SIZE
        if stage is None or at + ET.TEX_DESC_SIZE > len(td):
            continue
        api = td[at + ET.TEX_DESC_API]
        (swap,) = struct.unpack_from("<i", td, at + ET.TEX_DESC_SWAP)
        desc[(stage, api)] = (td[at + ET.TEX_DESC_TYPE], swap)
        if b in mm:
            mat[(stage, api)] = mm.index(b)
    return mat, desc


def effect_samplers(effect, smp_pairs: bytes):
    """(stage, api) -> S# words of the effect samplers of a pass (FUN_01447fa0)."""
    sd = effect[3]
    out = {}
    for j in range(0, len(smp_pairs) - 1, 2):
        stage = ET.STAGE_CODE.get(smp_pairs[j])
        at = smp_pairs[j + 1] * ET.SMP_DESC_SIZE
        if stage is None or at + ET.SMP_DESC_SIZE > len(sd):
            continue
        (api,) = struct.unpack_from("<I", sd, at + ET.SMP_DESC_API)
        out[(stage, api & 0xFF)] = list(struct.unpack_from("<4I", sd, at + ET.SMP_DESC_SHARP))
    return out


def material_textures(mat_map, desc, matinst, tex):
    """(stage, api) -> T# words of one material instance (FUN_0144a250 + FUN_0144a130)."""
    _f, _o, n_tex, tl = matinst
    out = {}
    for key, i in mat_map.items():
        words = None
        if (i + 1) * ET.MAT_TEX_ENTRY <= len(tl):
            (h,) = struct.unpack_from("<q", tl, i * ET.MAT_TEX_ENTRY)
            t = tex.get(h)
            if t is not None:
                words = ET.srgb_swap(list(t[0]), t[1], desc[key][1])
        if words is None:
            typ, df, nf, sel = ET.DEFAULT_TEXTURE
            words = words_of(["I", 1, typ, df, nf, list(sel)])
        out[key] = words
    return out


_PARTICLE_CACHE: Dict[str, Dict[int, int]] = {}


def particle_strides(ix: Index) -> Dict[int, int]:
    key = ix.root + "|" + str(len(ix.files))
    if key not in _PARTICLE_CACHE:
        _PARTICLE_CACHE[key] = _particle_strides(ix)
    return _PARTICLE_CACHE[key]


def _particle_strides(ix: Index) -> Dict[int, int]:
    """CS hash -> the state stride of the particle definition that holds it (u32 def+0x88);
    8,014 of the 8,049 compute shaders have exactly one plausible value (re_compute §3)."""
    by_file = defaultdict(dict)
    for f, hdr, h in ix.db.execute("SELECT file, hdr_off, hash FROM shader_occ WHERE stage = 'CS'"):
        by_file[f][hdr] = h & U64
    out = defaultdict(Counter)
    for f, hdrs in sorted(by_file.items()):
        with kcap.Pack(os.path.join(ix.root, ix.files[f][0])) as p:
            r0 = knli.read_links(p).positions(knli.RELOC_CPU)
            objs = {q - ET.SHADER_OBJ_HDR: hdrs[p.u64(q)] for q in r0 if p.u64(q) in hdrs}
            if not objs:
                continue
            a, b = ET.PARTICLE_KERNELS
            for q in r0:
                h = objs.get(p.u64(q))
                if h is None:
                    continue
                for k, other_k in ((a, b), (b, a)):
                    d = q - k
                    other = d + other_k
                    if other in r0 and p.u64(other) in objs and p.valid(d + ET.PARTICLE_STRIDE, 4):
                        out[h][p.u32(d + ET.PARTICLE_STRIDE)] += 1
                        break
    res = {}
    for h, c in out.items():
        c = {k: n for k, n in c.items() if 16 <= k <= 1024 and k % 16 == 0}
        if c:
            res[h] = max(c, key=c.get)
    return res


# --- generation ---------------------------------------------------------------------------
class Builder:
    def __init__(self, ix: Index, tables: ET.Tables, max_state=12, max_material=12, max_compute=8,
                 compute_model="re", compute_wide=False):
        self.ix, self.t = ix, tables
        self.compute_model, self.compute_wide = compute_model, compute_wide
        self.def_strides = None
        self.max_state, self.max_material, self.max_compute = max_state, max_material, max_compute
        self.stats = Counter()
        self.seen = set()

    def fallback(self, key: str, usage: int):
        w = self.t.fallback.get(key)
        if w is None:
            w = self.t.fallback.get(f"{usage}/*/{key.split('/')[2]}")
        if w is None:
            w = ["S", 0, 0] if usage == S.USAGE_SAMPLER else (
                ["I", 1, 9, 10, 0, [4, 5, 6, 7]] if key.endswith("/8") else
                ["B", 1, 16, 0, 0, 0, 4, 7, [4, 0, 0, 1], 4, 0])
            self.stats["fallback_default"] += 1
        return w

    def engine_choices(self, profiles, keys_vs, keys_ps, ph: S.Header, limit):
        """Joint (state, VS engine sharps, PS engine sharps) choices of a pass id, projected on
        the slots of this pair, most common first. Profiles of pixel shaders with the same
        export formats come first: on the capture (pass id, SPI_SHADER_COL_FORMAT) decides the
        whole state of the large groups (318 draws, one state)."""
        mask, colfmt = S.mrt_written(ph), ph.words["COL_FORMAT"]
        kv, kp = {k for k, _u in keys_vs}, {k for k, _u in keys_ps}
        cnt, keep, best = Counter(), {}, {}
        for p in profiles:
            st = p["state"]
            # closest draws first: same export formats, then the most slots in common
            sim = (p.get("colfmt") == colfmt,
                   len(kv & set(p["VS"])) / (len(kv) or 1) + len(kp & set(p["PS"])) / (len(kp) or 1))
            vsw = tuple((k, json.dumps(p["VS"].get(k) or self.fallback(k, u))) for k, u in keys_vs)
            psw = tuple((k, json.dumps(p["PS"].get(k) or self.fallback(k, u))) for k, u in keys_ps)
            key = (project_state(st, mask), vsw, psw)
            cnt[key] += 1
            best[key] = max(best.get(key, sim), sim)
            keep.setdefault(key, (restrict_state(st, mask), vsw, psw))
        ranked = sorted(cnt, key=lambda k: (best[k], cnt[k]), reverse=True)
        return [keep[k] for k in ranked[:limit]]

    def profiles_for(self, pid: int):
        ps = self.t.engine.get(pid)
        if ps:
            return ps
        self.stats["pass_id_without_profile"] += 1
        pooled = [p for lst in self.t.engine.values() for p in lst]
        return pooled

    def stage(self, sw, hw, h, flat_words: Dict[int, List[int]], hdr: S.Header, fetch=None):
        n = max([16] + [r + len(w) for r, w in flat_words.items()])
        flat = [0] * n
        for r, w in flat_words.items():
            flat[r:r + len(w)] = w
        st = {"sw": sw, "hw": hw, "hash": h, "code": self.ix.code(h), "ud": flat[:16], "flat": flat,
              "fetch": b"", "fetch_sgpr": 0, "vsharps": []}
        if fetch:
            st["fetch"], st["fetch_sgpr"], st["vsharps"] = fetch
        return st

    def vs_meshes(self, vs, fcode, vs_effects, mats, meshes):
        """Vertex V# of the meshes of every effect with this vertex shader, most common first:
        the fetch fallback when no mesh is tied to the pass's own effect (material instances
        linked by the game at run time)."""
        cnt, keep = Counter(), {}
        loads = fetch_loads(fcode)
        for eff in vs_effects.get(vs, ()):
            for m in mats.get(eff, []):
                for vsb in meshes.get((m[0], m[1]), []):
                    n = len(vsb) // 16
                    if any(off // 4 >= n for _sg, off in loads):
                        continue
                    attrs = tuple(tuple(struct.unpack_from("<4I", vsb, 16 * (off // 4))) for _sg, off in loads)
                    key = S.fetch_projection({"fetch": fcode, "vsharps": [(0, 0, a) for a in attrs]})
                    cnt[key] += 1
                    keep.setdefault(key, attrs)
        return [keep[k] for k, _ in cnt.most_common(self.max_material)]

    def graphics(self, groups, effects, mats, meshes, tex, vs_effects=None) -> Iterable[dict]:
        ix = self.ix
        total = len(groups)
        for gi, ((vs, ps, pid), rows) in enumerate(sorted(groups.items())):
            if gi % 200 == 0:
                print(f"PROGRESS jobs {gi} {total}", flush=True)
            vh, ph = ix.headers.get(vs), ix.headers.get(ps)
            if vh is None or ph is None or vh.stage != "VS" or ph.stage != "PS":
                self.stats["pair_without_header"] += 1
                continue
            vslots, pslots = sharp_slots(vh), sharp_slots(ph)
            fetch_slot = next((s for s in slot_list(vh) if s[0] == S.USAGE_FETCH), None)
            vb_slot = next((s for s in slot_list(vh) if s[0] == S.USAGE_VB_TABLE), None)
            # material/fetch tuples over the pass records of this pair and pass id
            mt_cnt, mt_keep = Counter(), {}
            fetch_codes = {}
            for (f, o, fo, fs, tp, sp, eff) in rows:
                fcode = ix.read(f, fo, fs) if fo is not None and fs else b""
                if fcode:
                    fetch_codes[hashlib.sha1(fcode).digest()] = fcode
                fkey = hashlib.sha1(fcode).digest() if fcode else b""
                if eff is None or eff not in effects:
                    key = (fkey, (), (), ())
                    mt_cnt[key] += 1
                    mt_keep.setdefault(key, (fcode, {}, {}, None))
                    continue
                e = effects[eff]
                mat_map, desc = material_bindings(e, tp)
                smp = effect_samplers(e, sp)
                for m in mats.get(eff, [None]):
                    mt = material_textures(mat_map, desc, m, tex) if m else {}
                    mesh_list = meshes.get((m[0], m[1]), []) if m else []
                    for vsb in (mesh_list or [None]):
                        attrs = ()
                        if fcode and vsb is not None:
                            n = len(vsb) // 16
                            attrs = tuple(tuple(struct.unpack_from("<4I", vsb, 16 * (off // 4)))
                                          if off // 4 < n else None for _sg, off in fetch_loads(fcode))
                        pkey = (fkey,
                                tuple(sorted((k, S.proj_image(w, False)) for k, w in mt.items())),
                                tuple(sorted((k, S.proj_sampler(w)) for k, w in smp.items())),
                                tuple(None if a is None else S.fetch_projection(
                                    {"fetch": b"x", "vsharps": [(0, 0, a)]})[1] for a in attrs))
                        mt_cnt[pkey] += 1
                        mt_keep.setdefault(pkey, (fcode, mt, smp, attrs if vsb is not None else None))
            # passes whose effect has no mesh: the meshes of other effects of the same VS
            for key in [k for k in mt_cnt if mt_keep[k][3] is None and mt_keep[k][0]]:
                fcode, mt, smp, _a = mt_keep[key]
                alts = self.vs_meshes(vs, fcode, vs_effects or {}, mats, meshes)
                if alts:
                    c = mt_cnt.pop(key)
                    del mt_keep[key]
                    for attrs in alts:
                        nk = key[:3] + (("vs", S.fetch_projection({"fetch": fcode, "vsharps": [(0, 0, a) for a in attrs]})),)
                        mt_cnt[nk] += c
                        mt_keep.setdefault(nk, (fcode, mt, smp, attrs))
                        self.stats["fetch_from_vs_meshes"] += 1
            choices = self.engine_choices(self.profiles_for(pid), [(k, u) for k, u, *_ in vslots],
                                          [(k, u) for k, u, *_ in pslots], ph, self.max_state)
            base_regs = header_regs(vh, ph)
            for mkey, _ in mt_cnt.most_common(self.max_material):
                fcode, mt, smp, attrs = mt_keep[mkey]
                for st, vsw, psw in choices:
                    regs = dict(base_regs)
                    regs.update(state_regs(st))
                    stages = []
                    for sw, hw, h, hdr, slots, eng in ((S_PS, H_PS, ps, ph, pslots, psw),
                                                        (S_VS, H_VS, vs, vh, vslots, vsw)):
                        stage_name = hdr.stage
                        eng = dict(eng)
                        words = {}
                        for key, usage, api, start, n in slots:
                            w = None
                            if usage in (S.USAGE_RESOURCE, S.USAGE_RW) and n == 8 and (stage_name, api) in mt:
                                w = mt[(stage_name, api)]
                                self.stats["sharp_material"] += 1
                            elif usage == S.USAGE_SAMPLER and (stage_name, api) in smp:
                                w = smp[(stage_name, api)]
                                self.stats["sharp_effect_sampler"] += 1
                            elif usage == S.USAGE_CB:
                                w = CB_WORDS
                                self.stats["sharp_cb"] += 1
                            else:
                                w = words_of(json.loads(eng[key]))
                                self.stats["sharp_engine"] += 1
                            words[start] = list(w)[:n]
                        fetch = None
                        if sw == S_VS and fcode and fetch_slot and vb_slot:
                            loads = fetch_loads(fcode)
                            sem = vs_input_semantics(vh)
                            vsh = []
                            for i, (sg, off) in enumerate(loads):
                                a = attrs[i] if attrs and i < len(attrs) and attrs[i] else None
                                if a is None:
                                    # INFERRED: (input semantic, size) -> the vertex format
                                    by_sem = (self.t.fallback.get(f"fetch/{sem[i][0]}/{sem[i][2]}")
                                              if i < len(sem) else None)
                                    a = tuple(words_of(by_sem or self.t.fallback.get("fetch") or
                                                       ["B", 1, 12, 0, 0, 0, 13, 7, [4, 5, 6, 7], 4, 0]))
                                    self.stats["fetch_fallback"] += 1
                                vsh.append((sg, off, tuple(a)))
                            fetch = (fcode, fetch_slot[2], vsh)
                        stages.append(self.stage(sw, hw, h, words, hdr, fetch))
                    rec = {"kind": 0, "regs": regs, "stages": stages}
                    sig = S.freeze(S.signature(rec, ix.headers))
                    if sig in self.seen:
                        self.stats["duplicate"] += 1
                        continue
                    self.seen.add(sig)
                    self.stats["graphics"] += 1
                    yield rec
        print(f"PROGRESS jobs {total} {total}", flush=True)

    def compute(self, hashes: Iterable[int]) -> Iterable[dict]:
        ix = self.ix
        if self.compute_model == "re" and self.def_strides is None:
            self.def_strides = particle_strides(ix)
        for h in sorted(hashes):
            hdr = ix.headers.get(h)
            if hdr is None or hdr.stage != "CS":
                continue
            slots = sharp_slots(hdr)
            variants = (self.compute_re(h, hdr, slots) if self.compute_model == "re"
                        else self.compute_profiles(hdr, slots))
            w = hdr.words
            regs = {0: 1, 1: 1, 2: 1, 3: 1, S.CS_NUM_THREAD_X: w["NUM_THREAD_X"],
                    S.CS_NUM_THREAD_X + 1: w["NUM_THREAD_Y"], S.CS_NUM_THREAD_X + 2: w["NUM_THREAD_Z"],
                    S.CS_RSRC1: w["RSRC1"], S.CS_RSRC2: w["RSRC2"]}
            for words in variants:
                st = self.stage(S_CS, H_CS, h, words, hdr)
                rec = {"kind": 1, "regs": dict(regs), "stages": [st]}
                sig = S.freeze(S.signature(rec, ix.headers))
                if sig in self.seen:
                    self.stats["duplicate"] += 1
                    continue
                self.seen.add(sig)
                self.stats["compute"] += 1
                yield rec

    def compute_re(self, h, hdr, slots):
        """The compute model of the re_compute report: one V# per slot from COMPUTE_SLOTS (the
        particle definition stride for (4,1), the code-derived stride where the table has none),
        and the previous-state V# in s[0:3] null and bound."""
        acc = gcn_mem.accesses(self.ix.code(h))
        dstride = self.def_strides.get(h)
        self.stats["cs_particle" if dstride else "cs_engine"] += 1
        base, s0 = {}, None
        for key, usage, api, start, n in slots:
            if usage == S.USAGE_CB:
                base[start] = CB_WORDS
                continue
            if key.startswith("implicit"):
                if start == 0:
                    s0 = (start, gcn_mem.written(acc, start), gcn_mem.code_stride(acc, start))
                else:
                    base[start] = ET.CS_NULL_VSHARP
                continue
            if usage in (S.USAGE_RESOURCE, S.USAGE_RW) and n == 4:
                rule = ET.COMPUTE_SLOTS.get((usage, api), "code")
                stride = dstride if rule == "def" else gcn_mem.code_stride(acc, start) if rule == "code" else rule
                if rule == "def" and stride is None:
                    stride = gcn_mem.code_stride(acc, start)
                if stride is None:
                    w = self.fallback(key, usage)
                    base[start] = words_of(w)[:n]
                    self.stats["cs_slot_fallback"] += 1
                    continue
                d3 = ET.CS_RW_DWORD3 if usage == S.USAGE_RW else ET.CS_RO_DWORD3
                base[start] = [0x100, stride << 16, 1, d3]
                continue
            base[start] = words_of(self.fallback(key, usage))[:n]   # images, samplers
            self.stats["cs_slot_fallback"] += 1
        if s0 is None:
            return [base]
        start, wr, cstride = s0
        out = [{**base, start: ET.CS_NULL_VSHARP}]
        if wr:
            strides = [1]
        else:
            strides = [cstride or dstride or 16]
            if self.compute_wide:
                strides += [x for x in (16, 4) if x not in strides]
        d3 = ET.CS_RW_DWORD3 if wr else ET.CS_RO_DWORD3
        for st in strides:
            out.append({**base, start: [0x100, st << 16, 1, d3]})
        return out

    def compute_profiles(self, hdr, slots):
        """Compute v0: the closest captured dispatches (INFERRED profiles)."""
        profiles = self.t.compute
        keys = [k for k, *_ in slots]
        cnt, keep = Counter(), {}
        kset = set(keys)
        nt = [hdr.words["NUM_THREAD_X"], hdr.words["NUM_THREAD_Y"], hdr.words["NUM_THREAD_Z"]]
        for p in profiles:
            shared = sum(k in p for k in keys)
            if keys and not shared:
                continue
            p_keys = set(p) - {"_nt"}
            rank = (p_keys == kset, p.get("_nt") == nt, shared)
            ws = tuple(json.dumps(p.get(k) or self.fallback(k, u)) for k, u, *_ in slots)
            cnt[ws] += 1
            keep[ws] = max(keep.get(ws, (False, False, 0)), rank)
        if not cnt:
            cnt[tuple(json.dumps(self.fallback(k, u)) for k, u, *_ in slots)] = 1
            self.stats["compute_without_profile"] += 1
        ranked = sorted(cnt, key=lambda ws: (keep.get(ws, (False, False, 0)), cnt[ws]), reverse=True)
        out = []
        for ws in ranked[:self.max_compute]:
            words = {}
            for (key, usage, api, start, n), wj in zip(slots, ws):
                words[start] = CB_WORDS if usage == S.USAGE_CB else words_of(json.loads(wj))[:n]
            out.append(words)
        return out


S_PS, S_VS, S_CS = jobfile.SW_FRAGMENT, jobfile.SW_VERTEX, jobfile.SW_COMPUTE
H_PS, H_VS, H_CS = jobfile.HW_FRAGMENT, jobfile.HW_VERTEX, jobfile.HW_COMPUTE


def build(index_path, tables: ET.Tables, *, game=None, pairs=None, cs=None, compute=True,
          graphics=True, **caps):
    """All records (a generator) and the builder (its .stats fill while iterating)."""
    ix = Index(index_path, game)
    b = Builder(ix, tables, **caps)

    def gen():
        if graphics:
            ctx = load_graphics_context(ix, pairs)
            yield from b.graphics(*ctx)
        if compute:
            hs = cs if cs is not None else [h for h, x in ix.headers.items() if x.stage == "CS"]
            yield from b.compute(hs)
        ix.close()
    return gen(), b


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m xpps.jobs", description=__doc__.split("\n")[0])
    ap.add_argument("index")
    ap.add_argument("tables", help="INFERRED tables (jobs_eval.py infer)")
    ap.add_argument("out")
    ap.add_argument("--game", help="folder of the .xpps files (default: the index root)")
    ap.add_argument("--max-state", type=int, default=12)
    ap.add_argument("--max-material", type=int, default=12)
    ap.add_argument("--max-compute", type=int, default=8, help="compute v0 (profiles) only")
    ap.add_argument("--compute-model", choices=("re", "profiles"), default="re")
    ap.add_argument("--compute-wide", action="store_true")
    ap.add_argument("--no-compute", action="store_true")
    ap.add_argument("--no-graphics", action="store_true")
    a = ap.parse_args(argv)
    recs, b = build(a.index, ET.Tables.load(a.tables), game=a.game, compute=not a.no_compute,
                    graphics=not a.no_graphics, max_state=a.max_state,
                    max_material=a.max_material, max_compute=a.max_compute,
                    compute_model=a.compute_model, compute_wide=a.compute_wide)
    n = jobfile.write(a.out, recs)
    print(json.dumps({"records": n, **b.stats}, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
