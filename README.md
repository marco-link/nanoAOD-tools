# nanoAOD-tools for WbWbX analysis

[![ST workflow](https://github.com/defranchis/nanoAOD-tools/actions/workflows/main.yml/badge.svg)](https://github.com/defranchis/nanoAOD-tools/actions/workflows/main.yml)

Tests (2017 only!) are defined in [test/runCMSSWTest_2017.sh](https://github.com/WbWbX/nanoAOD-tools/blob/defranchis/test/runCMSSWTest_2017.sh)

## Checkout instructions: CMSSW_11_1_7

```
export SCRAM_ARCH=slc7_amd64_gcc820
cmsrel CMSSW_11_1_7
cd CMSSW_11_1_7/src
git clone -b wbwbxUL git@github.com:<yourname>/nanoAOD-tools.git PhysicsTools/NanoAODTools
cd PhysicsTools/NanoAODTools
cmsenv
scram b
```

Note that only `CMSSW_11_X` or higher includes TensorFlow v2.1 which is used for training the b charge tagger. To check which TF version comes with CMSSW use ```scram tool list | grep tensorflow```.


## General instructions to run the post-processing step

The general post-processing script for producing final ntuples for plotting and statistical interpretation is:

```
python PhysicsTools/NanoAODTools/processors/ST.py \
    -i <root input file> \
    --year <year>  \
    [--isSignal] [--isData] [--nleptons <N>] [--nosys] [--notagger] \
    <output file name>
```

The script accepts the following arguments:
* `-i` the input root file is an extended nanoAOD format which includes additional information to evaluate the charge tagger on-the-fly. It is created using the [ChargeReco](https://github.com/WbWbX/ChargeReco) package.
* `--year` needs to be one of the following: '2016','2016preVFP','2017','2018' (default: '2016')
* `--nleptons` flag to switch between signal (=1) and top quark pair control region (=2) (default: 1)
* `--isSignal` optional flag to store additional information for the signal (e.g. parton/particle level observables, LHE weights) (default: false)
* `--isData` optional flag to remove gen-level information when running on data (default: false)
* `--nosys` optional flag to remove all systematics (default: false)
* `--notagger` optional flag to skip b charge tagger evaluation  (default: false)

## Analysis modules

The analysis-specific modules can be found under [python/modules](https://github.com/WbWbX/nanoAOD-tools/tree/wbwbxUL/python/modules).
In general, the input and output collections of modules should be configurable so that they can be easily reused, i.e. for evaluating systematics. A few important ones are
* MuonSelection/MuonVeto: modules to select tight isolated muon candidates and veto additional loose muons (similar modules exists for electrons). For MC, the module also produces weights to evaluate the uncertainties on the lepton selection and reconstruction efficiencies.
* JetMetUncertinties: module to evalutate JEC/JER/MET uncertainties. Separate collections of objects are created for each variation.
* JetSelection: module to select jets within acceptance
* ChargeTagging: evaluates the b jet charge tagger and attaches the result to the jet object

## BDT training

The following simple script is provided under [scripts/trainBDT.py](https://github.com/WbWbX/nanoAOD-tools/blob/wbwbxUL/scripts/trainBDT.py).

# Legacy analysis workflow by Marco

Run steps with `python processors/WbWbX.py --input <path to .root file> --step X` with `X=1, 2 or 3`!
See `python processors/WbWbX.py -h` for more options.


## step1

- [x] preskim (background only)
- [ ] particle selections/filters
- [ ] additional weights calculation
- [ ] scale factor calculation
- [x] Jetcharge from parton flavour
- [x] Wb generator (signal  only)
- [x] drop trigger information and more unused variables


## step2

- [x] leptonic W reconstruction
- [x] apply b tagging WP
- [ ] apply b charge tagger
- [x] drop special tagger variables


## step3

- [x] Event selection
- [x] Wb reconstruction
- [x] add smeared truth
- [x] apply binning for asymmetry


## plot (+ unfolding)



# The Asymmetry binning

-`bin > 0` onshell
-`bin < 0` offshell

- `abs(bin)==1` negative charge (bottom quark)
- `abs(bin)==2` positive charge (anti bottom quark)

- `bin == 0` zero charge


## General information on nanoaod-tools

### How to write and run modules

It is possible to import modules that will be run on each entry passing the event selection, and can be used to calculate new variables that will be included in the output tree (both in friend and full mode) or to apply event filter decisions.

We will use `python/postprocessing/examples/exampleModule.py` as an example. The module definition [file](python/postprocessing/examples/exampleModule.py), containing a simple constructor
```
   exampleModuleConstr = lambda : exampleProducer(jetSelection= lambda j : j.pt > 30)
```
should be imported using the following syntax:

```
python scripts/nano_postproc.py outDir /eos/cms/store/user/andrey/f.root -I PhysicsTools.NanoAODTools.postprocessing.examples.exampleModule exampleModuleConstr
```

Let us now examine the structure of the `exampleProducer` module class. All modules must inherit from `PhysicsTools.NanoAODTools.postprocessing.framework.eventloop.Module`.
* the `__init__` constructor function should be used to set the module options.
* the `beginFile` function should create the branches that you want to add to the output file, calling the `branch(branchname, typecode, lenVar)` method of `wrappedOutputTree`. `typecode` should be the ROOT TBranch type ("F" for float, "I" for int etc.). `lenVar` should be the name of the variable holding the length of array branches (for instance, `branch("Electron_myNewVar","F","nElectron")`). If the `lenVar` branch does not exist already - it can happen if you create a new collection, see an example [here](python/postprocessing/examples/collectionMerger.py)) - it will be automatically created.
* the `analyze` function is called on each event. It should return `True` if the event is to be retained, `False` if it should be dropped.

### Keep/drop branches
See the effect of keep/drop instructions by running:
```
python scripts/nano_postproc.py outDir /eos/cms/store/user/andrey/f.root -I PhysicsTools.NanoAODTools.postprocessing.examples.exampleModule exampleModuleConstr -s _exaModu_keepdrop --bi scripts/keep_and_drop_input.txt --bo scripts/keep_and_drop_output.txt
```
comparing to the previous command (without `--bi` and `--bo`).
The output branch created by _exampleModuleConstr_ produces the same result in both cases. But this one drops all other branches when creating output tree. It also runs faster.

The event interface, defined in `PhysicsTools.NanoAODTools.postprocessing.framework.datamodule`, allows to dynamically construct views of objects organized in collections, based on the branch names, for instance:

    electrons = Collection(event, "Electron")
    if len(electrons)>1: print electrons[0].someVar+electrons[1].someVar
    electrons_highpt = filter(lambda x: x.pt>50, electrons)

and this will access the elements of the `Electron_someVar`, `Electron_pt` branch arrays. Event variables can be accessed simply by `event.someVar`, for instance `event.rho`.

The output branches should be filled calling the `fillBranch(branchname, value)` method of `wrappedOutputTree`. `value` should be the desired value for single-value branches, an iterable with the correct length for array branches. It is not necessary to fill the `lenVar` branch explicitly, as this is done automatically using the length of the passed iterable.


### mht producer
Now, let's have a look at another example, `python/postprocessing/examples/mhtjuProducerCpp.py`, [file](python/postprocessing/examples/mhtjuProducerCpp.py). Similarly, it should be imported using the following syntax:

```
python scripts/nano_postproc.py outDir /eos/cms/store/user/andrey/f.root -I PhysicsTools.NanoAODTools.postprocessing.examples.mhtjuProducerCpp mhtju
```
This module has the same structure of its producer as `exampleProducer`, but in addition it utilizes a C++ code to calculate the mht variable, `src/mhtjuProducerCppWorker.cc`. This code is loaded in the `__init__` method of the producer.





