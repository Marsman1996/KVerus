#! /bin/bash

rm -rf build
mkdir -p build/bin

# Build for Verus processor
pushd processor/promex-verus
CARGO_TARGET_DIR=../../build cargo build --release || (echo "Test failed" && exit 1)
popd
cp build/release/PromeX-Verus build/bin
rm -rf build/release