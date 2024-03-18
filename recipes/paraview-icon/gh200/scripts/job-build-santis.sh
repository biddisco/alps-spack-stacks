#!/bin/bash

#SBATCH --job-name=stackinator-icon-cmake
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --partition=normal
#SBATCH --account=csstaff
#SBATCH --output=/users/biddisco/stackinator-output.txt
#SBATCH --error=/users/biddisco/stackinator-error.txt

export PYTHONUNBUFFERED=1

SRC=/users/biddisco/src
CLUSTER=santis
STACKI_DIR=$SRC/alps-vcluster/stackinator
RECIPE_DIR=$SRC/alps-vcluster/alps-spack-stacks/recipes/paraview-icon/gh200
SYSTEM_DIR=$SRC/alps-vcluster/alps-cluster-config/$CLUSTER
BUILD_DIR=/dev/shm/biddisco

echo "# -----------------------------------------"
echo "Setup/clean build dir"
rm   -rf ${BUILD_DIR}/*
mkdir -p ${BUILD_DIR}
mkdir -p ${BUILD_DIR}/tmp

echo "# -----------------------------------------"
echo "Execute stackinator"
$STACKI_DIR/bin/stack-config -s $SYSTEM_DIR -b ${BUILD_DIR} -r $RECIPE_DIR -c $RECIPE_DIR/cache-config.yaml --debug --develop

# build the squashfs image - bubblewrap is used inside the makefile
echo "# -----------------------------------------"
echo "Trigger build"
cd /dev/shm/biddisco
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin HOME=$HOME https_proxy=$https_proxy http_proxy=$http_proxy no_proxy="$no_proxy" make store.squashfs -j32

echo "# -----------------------------------------"
echo "Force push anything that was built successfully"
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin make cache-force

echo "# -----------------------------------------"
echo "Copy generated squashfs file"
DATE=$(date +%F)
ls -al /dev/shm/biddisco/store.squashfs
cp -f /dev/shm/biddisco/store.squashfs $SCRATCH/$CLUSTER-icon-cmake-$DATE.squashfs
echo "Generated file should be $SCRATCH/$CLUSTER-icon-cmake-$DATE.squashfs"

# -----------------------------------------
# debug : create a shell using the spack setup used to create the squashfs
# -----------------------------------------
$BUILD_DIR/bwrap-mutable-root.sh --tmpfs ~ --bind $BUILD_DIR/tmp /tmp --bind $BUILD_DIR/store /user-environment env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin https_proxy=$https_proxy http_proxy=$http_proxy no_proxy="$no_proxy" SPACK_SYSTEM_CONFIG_PATH=/user-environment/config /bin/bash --norc --noprofile

echo "# -----------------------------------------"
echo "# REMOVE THE CLEANUP WHEN DEBUGGING"
echo "# -----------------------------------------"
echo "Clean up the /dev/shm directories"
#rm -rf   ${BUILD_DIR}/*

