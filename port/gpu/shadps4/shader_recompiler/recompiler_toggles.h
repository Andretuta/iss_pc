// SPDX-FileCopyrightText: Copyright 2026 shadPS4 Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

// tlg: recompiler fixes ported from the Shadow of the Colossus native port
// (github.com/AjncSystem/ShadowOfTheColossus-PC, MIT/GPL-2.0, commits 6f0b3e56, debb0c49,
// e3227814 and its vendored shared_memory_barrier_pass.cpp at 70bb4385) and the env switches
// that turn them on or off for A/B tests. Each switch is read once. The ISS_/GR2_ names reach
// here as TLG_ (the probe aliases the port prefix at start-up).

#pragma once

#include <cstdint>
#include <cstdlib>
#include <string_view>
#include "common/elf_info.h"

namespace Shader::Toggles {

namespace Detail {
/// TLG_<name>=0/1 when set, otherwise the default (only evaluated then).
inline bool EnvFlag(const char* name, bool (*fallback)()) {
    const char* v = std::getenv(name);
    return v && *v ? std::atoi(v) != 0 : fallback();
}

inline bool AlwaysOn() {
    return true;
}

/// inFAMOUS Second Son (CUSA00223 EU/US disc, CUSA00004 US digital): the LDS barrier fixes are
/// aimed at its GPU particle smoke (iss_pc #7) and stay off for the other games until tested.
inline bool InfamousDefault() {
    const std::string_view serial = Common::ElfInfo::Instance().GameSerial();
    return serial == "CUSA00223" || serial == "CUSA00004";
}
} // namespace Detail

/// Workgroups smaller than one GCN wave (<64 threads) get LDS barriers like a 64-thread one.
/// TLG_LDS_SMALL=0/1; default on for inFAMOUS only.
inline bool SmallGroupLdsBarriers() {
    static const bool enabled = Detail::EnvFlag("TLG_LDS_SMALL", &Detail::InfamousDefault);
    return enabled;
}

/// Workgroups of several waves (multiples of 64) get subgroup barriers where the guest relies
/// on lockstep inside one wave. TLG_LDS_MULTI=0/1; default on for inFAMOUS only.
inline bool MultiWaveLdsBarriers() {
    static const bool enabled = Detail::EnvFlag("TLG_LDS_MULTI", &Detail::InfamousDefault);
    return enabled;
}

/// The LDS barrier pass treats a ReadLane with a constant lane in uniform flow as uniform when
/// it decides whether a branch is divergent (one-wave workgroups only). From Pink-shadPS4
/// (luizgustavs) via SotC. TLG_LDS_READLANE=0/1; default on for inFAMOUS only.
inline bool LdsUniformReadLane() {
    static const bool enabled = Detail::EnvFlag("TLG_LDS_READLANE", &Detail::InfamousDefault);
    return enabled;
}

/// S_WQM_B64 writes the source mask grown to whole quads (it was a no-op). TLG_WQM=0 restores
/// the no-op; default on for every game (correctness fix).
inline bool WholeQuadMode() {
    static const bool enabled = Detail::EnvFlag("TLG_WQM", &Detail::AlwaysOn);
    return enabled;
}

/// Bits for the shader binary cache version: shaders recompiled under other switches must not
/// be reused (the cache key only hashes the recompiler sources).
inline std::uint32_t ShaderBinarySalt() {
    return (SmallGroupLdsBarriers() ? 1u : 0u) | (MultiWaveLdsBarriers() ? 2u : 0u) |
           (LdsUniformReadLane() ? 4u : 0u) | (WholeQuadMode() ? 0u : 8u);
}

} // namespace Shader::Toggles
