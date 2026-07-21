#!/bin/bash
#
# Retry just the post-install hook for the paraview 6.1.1 gh200 recipe
# without rebuilding the Spack-installed dependencies.
#
# Run this from /dev/shm/biddisco (or adjust BUILD_DIR below).

set -e

BUILD_DIR=/dev/shm/$USER
RECIPE_DIR=$HOME/src/alps-vcluster/alps-uenv/recipes/paraview/6.1.1/gh200
SYSTEM_DIR=$HOME/src/alps-vcluster/alps-cluster-config/daint
STACKI_DIR=$HOME/src/alps-vcluster/stackinator

# By default wipe the ParaView CMake build dir to avoid stale CMake state.
# Use --no-wipe-build to preserve it when the failure was in the post-install
# shell steps after ParaView was already built.
WIPE_BUILD=1
for arg in "$@"; do
  case "$arg" in
    --no-wipe-build) WIPE_BUILD=0 ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

cd "$BUILD_DIR"

# Regenerate the Makefile, sandbox script, and post-install hook from the
# updated recipe. This does NOT rebuild the installed store/ packages.
$STACKI_DIR/bin/stack-config \
  -s "$SYSTEM_DIR" \
  -b "$BUILD_DIR" \
  -r "$RECIPE_DIR" \
  --develop \
  --mirror "$RECIPE_DIR/mirrors.yaml"

if [ "$WIPE_BUILD" -eq 1 ]; then
  # Wipe the ParaView CMake build dir so it doesn't cache the wrong compiler.
  rm -rf "$BUILD_DIR/store/temp/build/paraview"
fi

# Rerun only the post-install target.
env --ignore-environment PATH=/usr/bin:/bin:`pwd -P`/spack/bin HOME="$HOME" cluster=daint make post-install -j32
