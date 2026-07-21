---
name: build-uenv-stackinator
description: Build a uenv (SquashFS software-stack image) on Alps HPC systems using Stackinator and Spack. Use when the task involves creating, configuring, building, debugging, or iterating on a uenv — writing or editing a Stackinator recipe (config.yaml, compilers.yaml, environments.yaml, packages.yaml), running stack-config, building store.squashfs, resolving Spack concretization/build failures inside the bubblewrap sandbox, fixing runtime issues in views, or testing an image with `uenv run`.
---

# Building a uenv with Stackinator

A uenv is a SquashFS image containing a Spack-built software stack, mounted on Alps HPC nodes. Stackinator turns a *recipe* plus a *cluster config* into a build directory, then orchestrates the Spack build inside a bubblewrap sandbox.

## Prerequisites

- **Stackinator**: provides the `stack-config` CLI (e.g. installed at `/users/bcumming/software/stackinator`).
- **Cluster config**: system-specific config (externals, network) in a directory, e.g. `/users/bcumming/software/alps-cluster-config/daint/`. Supplied via `-s`.
- **Mirror config** (optional): YAML pointing at source/build caches, e.g. `/users/bcumming/software/mirrors.yaml`. Supplied via `--mirror`.
- **Build location**: must NOT be under `/tmp`, `$HOME`, or `/` (sandbox bind-mount restriction). Use `/dev/shm/$USER/build` for fast local builds.

## Build workflow

### Phase 0 — Check for prior build notes

When given an existing recipe as a starting point, **read `README.md` in the root of the recipe directory first** (if present). It records findings from the last build of this recipe — custom Spack packages that were created, concretization workarounds, external-package overrides, runtime fixes, and other gotchas. Use these notes as hints before configuring or building.

### Phase 1 — Configure

```bash
stack-config \
  -r /path/to/recipe/ \
  -s /path/to/cluster-config/ \
  -b /dev/shm/$USER/build \
  --mirror=/path/to/mirrors.yaml
```

Generates the build directory (Makefile + spack.yaml) and clones Spack.

### Phase 2 — Build

```bash
cd /dev/shm/$USER/build
env --ignore-environment PATH=/usr/bin:/bin:`pwd -P`/spack/bin HOME=$HOME make store.squashfs NJOBS=32
```

- `env --ignore-environment` guarantees a clean build environment.
- `NJOBS` controls parallelism; the build runs inside a bubblewrap sandbox.
- Output is `store.squashfs` — the final uenv image.

### Phase 3 — Record build notes

On a successful build, **create (or update) `README.md` in the root of the recipe directory** with notes about the build. This is the counterpart to Phase 0 — write down what a future build of this recipe would want to know. In particular:
- **Custom Spack packages** created in `repo/` — what they are, why they were needed, and what they change (patches, variants, versions). Call these out explicitly; they are the most valuable notes.
- Concretization workarounds (unify strategy, pinned versions, variant flags).
- External-package overrides added to `packages.yaml` and why.
- Post-install / pre-install hooks and what they fix.
- Runtime fixes applied and any host dependencies the image relies on.
- Anything surprising or hard-won during the build.

Keep it concise and factual — it is a build log for the next person (or the next build), not user-facing documentation. If a `README.md` already exists, update the relevant sections rather than overwriting wholesale.

### Iterating

Edit recipe YAML → re-run `stack-config` → re-run `make store.squashfs`. Individual targets speed up iteration:
- `make concretize` — resolve dependencies only (check concretization).
- `make install` — build packages.
- `make store.squashfs` — package the image.

For rapid prototyping (e.g. testing a script change), edit files directly in the store path (`$BUILD/store/`) and re-run `make store.squashfs` — repackaging takes seconds. Once validated, implement the change properly in the recipe (post-install hook, custom package, etc.).

## Recipe structure

A recipe is a directory of YAML files. See `references/recipe-files.md` for the full field-by-field breakdown, examples, and key decisions for each of:
- `config.yaml` (required) — name, store/mount point, spack version, default-view, cleanup, version.
- `compilers.yaml` (required) — compiler versions; `"system"` skips building gcc.
- `environments.yaml` (required) — specs, compiler, unify strategy, network/mpi, and views.
- `packages.yaml` (optional) — external package overrides.
- `modules.yaml` (optional) — module file generation.
- `repo/` (optional) — custom Spack packages (last resort — prefer fixing upstream via variants/specs/externals).
- `post-install` / `pre-install` (optional) — shell scripts run inside the sandbox before/after the Spack build.

Read `references/recipe-files.md` before writing or editing any recipe file.

## Cluster config

Provided via `-s`; not authored per-recipe but must be understood:
- `packages.yaml` — system external packages. **Must include `gcc`** (with `extra_attributes.compilers` paths).
- `network.yaml` — MPI/network libraries. Irrelevant for non-MPI stacks.

## Debugging

- **Failed package logs**: the sandbox mounts `$BUILD/tmp` at `/tmp`. Spack prints log paths as `/tmp/...` but the real file is at `$BUILD/tmp/...`. E.g. a reported `/tmp/$USER/spack-stage/.../foo.log` lives at `/dev/shm/$USER/build/tmp/$USER/spack-stage/.../foo.log`. Check the tail for the real compile/link error.
- **Stackinator configure log**: `/tmp/$USER/log_stackinator_*`.
- **Debug shell inside the sandbox**: run `./stack-debug.sh` in the build directory.
- **Run commands non-interactively in the sandbox**: `stack-debug.sh` opens an *interactive* shell. To script the exact build environment — query the store DB, run `jq`, patch files, compile a test — copy the `env … bwrap-mutable-root.sh …` line from `stack-debug.sh` and replace the trailing `bash -noprofile -l` with `bash -noprofile -lc "<commands>"`. This is the reliable way to inspect or edit the store before repackaging: the store only exists at its mount point (`/user-environment`) *inside* the sandbox. Resolve a package's concrete prefix from the store DB with `spack find --format "{prefix}" "<spec>"`.
- **Spack directly**: `cd $BUILD && spack -e . find` or `spack -e . spec <package>`.

## Common issues

- **Concretization failures**: conflicting package requirements. Try `unify: when_possible` or adjust variant flags.
- **Missing externals**: if Spack builds something that should come from the system, add it to the recipe `packages.yaml` with `buildable: false`.
- **Build path restrictions**: cannot use `/tmp`, `$HOME`, or `/`.
- **Large images**: use `cleanup: runtime` (config.yaml), `link: run` in views, and avoid heavy deps (e.g. `mesa~llvm` to skip LLVM).
- **Custom-package post-install steps must be idempotent**: Stackinator builds a package, pushes it to the build cache, then reinstalls it from the cache — so a custom package's `@run_after("install")` file mutation (and other install-time file edits) can run *more than once* on the same prefix. A non-idempotent in-place edit (appending a block, injecting an rpath line) corrupts the file on the second pass, and the failure surfaces far downstream. Regenerate from a preserved pristine copy, or guard so re-application is a no-op.

## Fixing runtime issues

When a uenv builds but packages fail at runtime, escalate through these approaches (see `references/runtime-fixes.md` for detail):
1. **Missing files in the view** — only explicit specs (and their runtime deps) get linked. Add the needed package as an explicit spec (e.g. a transitive dep whose files must appear in `XDG_DATA_DIRS`).
2. **Environment variables** — set them in the view definition (`env.set` / `env.prepend_path`) in `environments.yaml`.
3. **Post-install hook** — arbitrary modifications: edit `meta/env.json`, patch installed prefixes, add wrapper scripts. May require a clean rebuild.
4. **Custom package** — last resort, only when the fault is in the Spack package's build logic.

## Post-install source builds

Sometimes a recipe's `post-install` hook needs to build additional software from source using the dependencies Spack just installed (e.g. an application version that is not available as a Spack package). The build environment must use the **exact** dependency versions that were installed, and must expose them to CMake/autotools.

### What does not work

- **`spack env activate`** only prepares the environment view for interactive use. It adds the view to `PATH`, but it does **not** set `CMAKE_PREFIX_PATH`, compiler flags, `PKG_CONFIG_PATH`, or other build-specific variables.
- **Synthetic packages + re-concretization**: generating a fake Spack package that `depends_on` all the recipe specs, adding it to the environment, and running `spack build-env` can pick different dependency versions than the ones that are actually installed. `spack build-env --reuse` helps, but concretization can still diverge.

### Recommended pattern: build the environment from installed prefixes

Query the store directly and construct the build environment manually. This guarantees the build uses the exact prefixes Spack installed. A reusable helper script is:

```bash
source $RECIPE/scripts/setup-spack-build-env.sh \
    -C {{ env.config }} \
    -e ${RECIPE_BUILD}/env/
```

The helper exports `CMAKE_PREFIX_PATH`, `PATH`, `PKG_CONFIG_PATH`, `CUDA_HOME`, `CC`/`CXX`/`FC`, and `PYTHONPATH` from the installed prefixes. The equivalent inline logic is:

```bash
STACKINATOR_ENV=${RECIPE_BUILD}/env/

# Installed prefixes, with color disabled and system prefixes removed.
INSTALLED_PREFIXES=$($SPACK_CMD --color=never -e ${STACKINATOR_ENV} find --format "{prefix}" | grep -vE '^/(usr)?$')

export CMAKE_PREFIX_PATH=$(echo "$INSTALLED_PREFIXES" | paste -sd ':')

while IFS= read -r prefix; do
    [ -d "${prefix}/bin" ] && PATH="${prefix}/bin:${PATH}"
done <<< "$INSTALLED_PREFIXES"
export PATH

PKG_CONFIG_PATH=""
for subdir in lib/pkgconfig lib64/pkgconfig share/pkgconfig; do
    while IFS= read -r prefix; do
        [ -d "${prefix}/${subdir}" ] && PKG_CONFIG_PATH="${prefix}/${subdir}:${PKG_CONFIG_PATH}"
    done <<< "$INSTALLED_PREFIXES"
done
[ -n "$PKG_CONFIG_PATH" ] && export PKG_CONFIG_PATH

for prefix in $(echo "$CMAKE_PREFIX_PATH" | tr ':' ' '); do
    [ -x "${prefix}/bin/nvcc" ] && export CUDA_HOME="${prefix}" && break
done

export CC=$(command -v gcc)
export CXX=$(command -v g++)
export FC=$(command -v gfortran || true)

PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHONPATH=""
while IFS= read -r prefix; do
    for pydir in "lib/python${PYTHON_VERSION}/site-packages" "lib64/python${PYTHON_VERSION}/site-packages"; do
        [ -d "${prefix}/${pydir}" ] && PYTHONPATH="${prefix}/${pydir}:${PYTHONPATH}"
    done
done <<< "$INSTALLED_PREFIXES"
[ -n "$PYTHONPATH" ] && export PYTHONPATH
```

Critical gotchas:

- **Use `--color=never`**. Spack's ANSI color codes (e.g. `[0;90m... [0m`) corrupt captured paths and cause every `prefix/bin` check to fail.
- **Filter `/` and `/usr`**. External/system packages can have these prefixes; adding their `bin/` directories to `PATH` places `/usr/bin` ahead of Spack tools and causes `cmake`, `python`, etc. to resolve to the system versions.
- **The environment path**: in current stackinator versions the active Spack environment is at `${RECIPE_BUILD}/env/`, not `${RECIPE_BUILD}/environments/<name>/`.
- **Set `CC`/`CXX` explicitly**. CMake defaults to the system `cc`/`c++` symlinks if these are not set, even when the Spack compiler is first on `PATH`.
- **Set `PYTHONPATH`**. Python packages such as `py-mpi4py` and `py-numpy` each live in their own Spack prefix; the interpreter will not find them unless their `lib/pythonX.Y/site-packages` directories are on `PYTHONPATH`.

The ParaView recipe provides a reusable helper at `scripts/setup-spack-build-env.sh`.

### ParaView-specific gotchas

- **Helper script paths inside the sandbox**: the post-install hook runs inside the bubblewrap sandbox. Recipe files are available at `${RECIPE_BUILD}/store/meta/recipe/` (not `${HOME}/store/meta/recipe`, because the retry script sets `HOME` to the user's home). Use `${RECIPE_BUILD}/store/meta/recipe/scripts/...` and `${RECIPE_BUILD}/store/meta/recipe/helpers/`.
- **HDF5 module rename**: VTK's internal HDF5 module is renamed from `VTK::hdf5` to `VTK::hdf5vtk` to avoid a CMake target conflict. Plugin `vtk.module` files must be patched accordingly.
- **Kokkos/Trilinos CUDA arch**: the recipe requests `cuda_arch=90a` for most packages, but Kokkos and Trilinos do not recognize `90a`. `packages.yaml` overrides them to `cuda_arch=90`.
- **Local git submodules**: the CSCS plugins repo includes one submodule (`pv-splotch`) that points to a local filesystem path. `git submodule update --init` for that repo must be run with `GIT_ALLOW_PROTOCOL=file:https` so Git allows both `file://`-like local paths and `https://` URLs.
- **pv-splotch and newer CUDA**: the `fbo-render-pass` branch uses `cudaDeviceProp.clockRate` and `cudaDeviceProp.deviceOverlap`, which were removed in newer CUDA toolkits. The post-install patches this diagnostic code out.

### ParaView plugins in this recipe

The recipe builds ParaView plugins as **external** plugins after ParaView is installed, using a dedicated CSCS plugins repository (`/capstor/store/cscs/cscs/csstaff/biddisco/gitrepos/plugins`). The repo includes:

- `pv-zoltan`
- `pv-meshless`
- `pv-splotch`
- `ParaViewGadgetPlugin` (the Gadget HDF5 reader)

These are configured, built, and installed in the post-install hook. Because the ParaView/VTK source tree renames the internal HDF5 module from `VTK::hdf5` to `VTK::hdf5vtk`, any plugin `vtk.module` files that still reference `VTK::hdf5` are patched during post-install.

Plugin discovery at runtime relies on `PV_PLUGIN_PATH`, which is set in the uenv view and in the generated `rc-submit-pvserver.sh` launch script:

```bash
export PV_PLUGIN_PATH=$PARAVIEW_PLUGINS_DIR:$PARAVIEW_PLUGINS_DIR/lib64:$PARAVIEW_PLUGINS_DIR/lib64/paraview/plugins
```

### Recipe generation workflow

This recipe uses a small generator (`gen-all.sh`) that produces `6.1.1/` from templates in `templates/`. Edits should usually be made to the templates (e.g. `templates/post-install-gh200`, `templates/environments.yaml`, `templates/packages.yaml`) and then regenerated with:

```bash
python3 ../generator/generate_recipe.py -m mpich -c gcc -C daint -r paraview -t ./templates -o ./6.1.1
```

Inside the templates, avoid using `${RECIPE}` as a shell variable name because the generator substitutes it with the recipe name (`paraview`). Use `${RECIPE_BUILD}` instead.

## Testing images

**Verify the headline feature actually works — not just that the build finished.** A build can complete successfully while its main capability is broken (e.g. a compiler that builds but can't link or run its target, a plugin that isn't on the view's search path). Exercise the real workflow end-to-end: compile *and run* a representative program, load the library, drive the tool — don't stop at "the binary is on `PATH`". If the image's purpose is offload/GPU, run something that forces the GPU (e.g. `OMP_TARGET_OFFLOAD=MANDATORY`) so a silent host fallback fails loudly.

Use `uenv run` (NOT `uenv start`) to test a built image:

```bash
# Run a command inside the uenv (default-view applies automatically if set in config.yaml)
uenv run /dev/shm/$USER/build/store.squashfs -- which Xvnc

# Specify a view name explicitly when there is no default-view
uenv run /dev/shm/$USER/build/store.squashfs vnc -- which Xvnc

# Inspect available views
uenv inspect /dev/shm/$USER/build/store.squashfs
```

## Reference material

- `references/recipe-files.md` — full recipe file reference with annotated examples and per-field decisions.
- `references/runtime-fixes.md` — detailed runtime-issue remediation.
- `references/vnc-example.md` — worked example: design decisions for a VNC/remote-visualization uenv on GH200 (what to bundle, what to rely on from the host, GPU/EGL notes).
