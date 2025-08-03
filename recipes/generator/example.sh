# paraview generation
pushd $SRC/alps-vcluster/alps-uenv/recipes/paraview

python ../generator/generate_recipe.py -m mpich -c gcc -C oryx  -r paraview -v egl    -t ./templates -o ./5.13.2
python ../generator/generate_recipe.py -m mpich -c gcc -C daint -r paraview -v egl    -t ./templates -o ./5.13.2
python ../generator/generate_recipe.py -m mpich -c gcc -C eiger -r paraview -v osmesa -t ./templates -o ./5.13.2

popd

# jb dev project generation
pushd $SRC/alps-vcluster/alps-uenv/recipes/jbdev

python ../generator/generate_recipe.py -m mpich -c gcc -C daint -r jbdev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C daint -r jbdev -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C eiger -r jbdev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C eiger -r jbdev -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C oryx -r jbdev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C oryx -r jbdev -t ./templates -o ./ompi

popd
