pushd $SRC/alps-vcluster/alps-uenv/recipes/paraview

python ../generator/generate_recipe.py -m mpich -a turing -c gcc -C oryx  -v egl    -t ./templates -r paraview -o ./5.13.2
python ../generator/generate_recipe.py -m mpich -a gh200  -c gcc -C daint -v egl    -t ./templates -r paraview -o ./5.13.2
python ../generator/generate_recipe.py -m mpich -a mc     -c gcc -C eiger -v osmesa -t ./templates -r paraview -o ./5.13.2

popd
