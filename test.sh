#!/bin/bash

python2 processors/WbWbX.py --isSignal ${filter} --year 2016 -N 1000  --input data/test/ST_4f_w_lo.root .
python2 processors/WbWbX.py            ${filter} --year 2016 -N 1000 --input data/test/TTToSemiLeptonic_TuneCP5_PSweights_13TeV-powheg-pythia8.root .
