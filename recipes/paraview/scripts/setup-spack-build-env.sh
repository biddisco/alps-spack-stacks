#!/bin/bash
#
# Set up a CMake/autotools build environment from a stackinator/Spack
# environment's installed packages.
#
# This is meant to be sourced from a post-install hook (or from an interactive
# shell inside the sandbox). It queries the store directly, so the build uses
# the exact dependency versions that were installed -- no re-concretization.
#
# Usage (from a post-install hook):
#   source $RECIPE/scripts/setup-spack-build-env.sh \
#       -C {{ env.config }} -e ${RECIPE_BUILD}/env/
#
# The script exports:
#   CMAKE_PREFIX_PATH  -- all installed dependency prefixes
#   PATH               -- bin/ directories of installed packages
#   PKG_CONFIG_PATH    -- pkgconfig directories of installed packages
#   CUDA_HOME          -- prefix containing nvcc (if any)
#   CC, CXX, FC        -- Spack compilers (gcc/g++/gfortran)
#   PYTHONPATH         -- site-packages of installed Python packages

set -e

function usage() {
    echo "Usage: source setup-spack-build-env.sh -C <spack-config> -e <env-path>"
    echo "  -C, --config   Spack config directory (passed to 'spack -C')"
    echo "  -e, --env      Path to the stackinator Spack environment"
}

SPACK_CONFIG=""
ENV_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -C|--config)
            SPACK_CONFIG="$2"
            shift 2
            ;;
        -e|--env)
            ENV_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            return 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            return 1
            ;;
    esac
done

if [ -z "$ENV_PATH" ]; then
    echo "Error: --env is required" >&2
    usage >&2
    return 1
fi

SPACK_CMD="spack"
if [ -n "$SPACK_CONFIG" ]; then
    SPACK_CMD="$SPACK_CMD -C $SPACK_CONFIG"
fi

# Query the installed prefixes. --color=never is essential: Spack's ANSI codes
# corrupt captured paths and break every subsequent prefix/bin check.
INSTALLED_PREFIXES=$($SPACK_CMD --color=never -e "$ENV_PATH" find --format "{prefix}" | grep -vE '^/(usr)?$')

if [ -z "$INSTALLED_PREFIXES" ]; then
    echo "Error: no installed prefixes found in $ENV_PATH" >&2
    return 1
fi

# CMake finds dependency config files here.
export CMAKE_PREFIX_PATH=$(echo "$INSTALLED_PREFIXES" | paste -sd ':')

# Put dependency bin/ directories on PATH (cmake, ninja, python, compilers, ...).
while IFS= read -r prefix; do
    if [ -d "${prefix}/bin" ]; then
        PATH="${prefix}/bin:${PATH}"
    fi
done <<< "$INSTALLED_PREFIXES"
export PATH

# Set up pkg-config search paths for autotools-style dependencies.
PKG_CONFIG_PATH=""
for subdir in lib/pkgconfig lib64/pkgconfig share/pkgconfig; do
    while IFS= read -r prefix; do
        if [ -d "${prefix}/${subdir}" ]; then
            PKG_CONFIG_PATH="${prefix}/${subdir}:${PKG_CONFIG_PATH}"
        fi
    done <<< "$INSTALLED_PREFIXES"
done
if [ -n "$PKG_CONFIG_PATH" ]; then
    export PKG_CONFIG_PATH
fi

# CUDA support: point CUDA_HOME at the prefix that provides nvcc.
for prefix in $(echo "$CMAKE_PREFIX_PATH" | tr ':' ' '); do
    if [ -x "${prefix}/bin/nvcc" ]; then
        export CUDA_HOME="${prefix}"
        break
    fi
done

# Make sure CMake uses the Spack compilers, not the system cc/c++.
export CC=$(command -v gcc)
export CXX=$(command -v g++)
export FC=$(command -v gfortran || true)

# Protobuf >= 22 headers include Abseil, but VTK/ParaView's FindProtobuf does
# not propagate Abseil include dirs. Add it to CXXFLAGS as a workaround.
ABSEIL_PREFIX=$(echo "$INSTALLED_PREFIXES" | grep '/abseil-cpp-' | head -n1)
if [ -n "$ABSEIL_PREFIX" ] && [ -d "${ABSEIL_PREFIX}/include" ]; then
    export CXXFLAGS="${CXXFLAGS:+$CXXFLAGS }-isystem ${ABSEIL_PREFIX}/include"
fi

# External Viskores built with CUDA exposes VISKORES_ENABLE_CUDA in its headers,
# but VTK/Accelerators/Vtkm does not always propagate the CUDA toolkit include
# path. Add it to CXXFLAGS as a workaround.
if [ -n "${CUDA_HOME}" ] && [ -d "${CUDA_HOME}/include" ]; then
    export CXXFLAGS="${CXXFLAGS:+$CXXFLAGS }-isystem ${CUDA_HOME}/include"
fi

# Python packages (mpi4py, numpy, ...) live in separate Spack prefixes.
# Add every installed site-packages directory to PYTHONPATH.
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHONPATH=""
while IFS= read -r prefix; do
    for pydir in "lib/python${PYTHON_VERSION}/site-packages" "lib64/python${PYTHON_VERSION}/site-packages"; do
        if [ -d "${prefix}/${pydir}" ]; then
            PYTHONPATH="${prefix}/${pydir}:${PYTHONPATH}"
        fi
    done
done <<< "$INSTALLED_PREFIXES"
if [ -n "$PYTHONPATH" ]; then
    export PYTHONPATH
fi
