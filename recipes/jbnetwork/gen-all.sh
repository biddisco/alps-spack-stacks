python ../generator/generate_recipe.py -m mpich -c gcc -C daint -r jbnetwork -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C daint -r jbnetwork -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C eiger -r jbnetwork -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C eiger -r jbnetwork -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C oryx -r jbnetwork -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C oryx -r jbnetwork -t ./templates -o ./ompi
