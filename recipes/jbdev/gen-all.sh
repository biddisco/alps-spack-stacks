python ../generator/generate_recipe.py -m mpich -c gcc -C daint -r jbdev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C daint -r jbdev -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C eiger -r jbdev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C eiger -r jbdev -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C oryx -r jbdev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C oryx -r jbdev -t ./templates -o ./ompi
