python ../generator/generate_recipe.py -m mpich -c gcc -C daint -r jb-dev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C daint -r jb-dev -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C eiger -r jb-dev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C eiger -r jb-dev -t ./templates -o ./ompi

python ../generator/generate_recipe.py -m mpich -c gcc -C oryx -r jb-dev -t ./templates -o ./mpich
python ../generator/generate_recipe.py -m ompi  -c gcc -C oryx -r jb-dev -t ./templates -o ./ompi

