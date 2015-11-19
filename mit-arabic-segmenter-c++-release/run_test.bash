#!/bin/bash

set -e

mkdir output

#### DEMO 1: Basic Training
#
# Trains Model 1 to 4 with random seed 0
./train.bash 0 atb.tiny output/atb.tiny-r0

#### DEMO 2: Maximium marginal decoding produces more robust segmentations
#
# Step 1: train with different random restarts
for r in $(seq 1 4); do
    ./train.bash $r atb.tiny output/atb.tiny-r$r
done
# Step 2: performs max-marginal decoding for each model 1 to 4
# Note: tags, stem_indices in merged dictionary becomes meaningless, 
#       so the dictionary can't be used to initialize MODEL > 1 anymore
./mmtrain.bash 5 atb.tiny output/atb.tiny

#### DEMO 3: Incremental training options
#
# Say we train Model 1 to 4 to produce dictionaries
# tahyyes.small-m{1,2,3,4}.dict
./train.bash 0 tahyyes.small output/tahyyes.small
#
# Now we have new data tahyyes.part2
#
# Option 1:
./incr_train1.bash tahyyes.part2 output/tahyyes.part2-inc1 tahyyes.small output/tahyyes.small-m1.dict
#
# Option 2:
# f in :stf means freeze words
./incr_train2.bash tahyyes.part2 output/tahyyes.part2-inc2 tahyyes.small output/tahyyes.small-m{1,2,3,4}.dict
#
# Option 3:
./incr_train3.bash tahyyes.part2 output/tahyyes.part2-inc3 output/tahyyes.small-m{1,2,3,4}.dict
#
# Option 4:
./incr_train4.bash tahyyes.part2 output/tahyyes.part2-inc4 output/tahyyes.small-m{1,2,3,4}.dict
#
# end DEMO 3

# Checking if your output matches mine
for my_dict in output.expected/*dict; do
    your_dict=$(echo ${my_dict} | sed "s/.expected//")
    if diff -q ${my_dict} ${your_dict}; then
        echo "dictionary ${your_dict} OK"
    fi
done
