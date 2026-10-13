#!/usr/bin/env bash
# Builds the libraries Ubuntu 24.04 lacks or ships too old for the port, into $PREFIX
# (default /opt/tlgdeps): SDL3, Zydis 5, fmt 11 and a minimal FFmpeg (only the H.264, MP3 and
# PNG decoders the runtime uses, instead of the distribution's ~250-library FFmpeg).
# Used by the GitHub Actions Linux build; the resulting .so files ship in the package (out/lib).
set -euo pipefail
PREFIX=${PREFIX:-/opt/tlgdeps}
JOBS=$(nproc)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"

fetch() { # url dir
    mkdir -p "$2" && curl -fsSL "$1" | tar -xz -C "$2" --strip-components=1
}

fetch https://github.com/libsdl-org/SDL/releases/download/release-3.2.24/SDL3-3.2.24.tar.gz sdl
cmake -S sdl -B sdl/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DSDL_SHARED=ON -DSDL_STATIC=OFF -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF
ninja -C sdl/build install

git clone -q --depth 1 --branch v5.0.0 --recursive https://github.com/zyantific/zydis.git zydis
cmake -S zydis -B zydis/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DZYDIS_BUILD_SHARED_LIB=ON -DZYDIS_BUILD_EXAMPLES=OFF -DZYDIS_BUILD_TOOLS=OFF -DZYDIS_BUILD_TESTS=OFF \
    -DZYDIS_BUILD_DOXYGEN=OFF
ninja -C zydis/build install

fetch https://github.com/fmtlib/fmt/archive/refs/tags/11.2.0.tar.gz fmt
cmake -S fmt -B fmt/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DBUILD_SHARED_LIBS=ON -DFMT_TEST=OFF -DFMT_DOC=OFF
ninja -C fmt/build install

fetch https://ffmpeg.org/releases/ffmpeg-7.1.2.tar.gz ffmpeg
(cd ffmpeg && ./configure --prefix="$PREFIX" --enable-shared --disable-static --disable-programs \
    --disable-doc --disable-network --disable-autodetect --enable-zlib --disable-everything \
    --enable-decoder=h264,mp3,mp3float,png --enable-parser=h264,mpegaudio,png \
    --enable-demuxer=h264,mp3,image2 --enable-protocol=file \
    --enable-avcodec --enable-avformat --enable-avutil --enable-swscale --enable-swresample \
    && make -j"$JOBS" && make install)
echo "Dependencies in $PREFIX"
