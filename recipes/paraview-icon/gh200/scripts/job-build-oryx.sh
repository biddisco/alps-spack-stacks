#!/bin/bash

#SBATCH --job-name=stackinator-paraview
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --partition=nvgpu
#SBATCH --account=csstaff
#SBATCH --output=/users/biddisco/stackinator-output.txt
#SBATCH --error=/users/biddisco/stackinator-error.txt

export PYTHONUNBUFFERED=1

CLUSTER=oryx
STACKI_DIR=$SRC/alps-vcluster/stackinator
RECIPE_DIR=$SRC/alps-vcluster/alps-spack-stacks/recipes/paraview-icon/gh200
SYSTEM_DIR=$SRC/alps-vcluster/alps-cluster-config/$CLUSTER
BUILD_DIR=/dev/shm/biddisco
MOUNT=/user-environment

echo "# -----------------------------------------"
echo "Setup/clean build dir"
#rm -rf   ${BUILD_DIR}/*
mkdir -p ${BUILD_DIR}
mkdir -p ${BUILD_DIR}/tmp

echo "# -----------------------------------------"
echo "Execute stackinator"
$STACKI_DIR/bin/stack-config -s $SYSTEM_DIR -b ${BUILD_DIR} -r $RECIPE_DIR -c $RECIPE_DIR/cache-config.yaml --debug --develop

# build the squashfs image - bubblewrap is used inside the makefile
echo "# -----------------------------------------"
echo "Trigger build"
pushd /dev/shm/biddisco
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin HOME=$HOME https_proxy=$https_proxy http_proxy=$http_proxy no_proxy="$no_proxy" make store.squashfs -j32

echo "# -----------------------------------------"
echo "Force push anything that was built successfully"
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin make cache-force

echo "# -----------------------------------------"
echo "Copy generated squashfs file"
DATE=$(date +%F)
unalias cp
cp -f /dev/shm/biddisco/store.squashfs $SCRATCH/$CLUSTER-icon-dsl-$DATE.squashfs

# -----------------------------------------
# debug : create a shell using the spack setup used to create the squashfs
# -----------------------------------------
#$BUILD_DIR/bwrap-mutable-root.sh --tmpfs ~ --bind $BUILD_DIR/tmp /tmp --bind $BUILD_DIR/store /user-environment env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin SPACK_SYSTEM_CONFIG_PATH=/user-environment/config /bin/bash --norc --noprofile

env --ignore-environment PATH=/usr/bin:/bin:/dev/shm/biddisco/spack/bin HOME=$HOME SOFTWARE_STACK_PROJECT=/dev/shm/biddisco STORE=$MOUNT SPACK_SYSTEM_CONFIG_PATH=/dev/shm/biddisco/config SPACK_USER_CACHE_PATH=/dev/shm/biddisco/cache SPACK=spack SPACK_COLOR=always SPACK_USER_CONFIG_PATH=/dev/null LC_ALL=en_US.UTF-8 TZ=UTC SOURCE_DATE_EPOCH=315576060 /dev/shm/biddisco/bwrap-mutable-root.sh --tmpfs ~ --bind /dev/shm/biddisco/tmp /tmp --bind /dev/shm/biddisco/store $MOUNT bash -noprofile -l



echo "# -----------------------------------------"
echo "# REMOVE THE CLEANUP WHEN DEBUGGING"
echo "# -----------------------------------------"
echo "Clean up the /dev/shm directories"
#rm -rf   ${BUILD_DIR}/*

# popd

