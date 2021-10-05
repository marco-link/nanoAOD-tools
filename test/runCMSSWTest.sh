function run_test()
{
    cd ~
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    export SCRAM_ARCH=slc7_amd64_gcc820 || return 1
    scramv1 project CMSSW CMSSW_11_1_7 || return 1
    cd CMSSW_11_1_7/src || return 1
    eval `scram runtime -sh` || return 1
    mkdir -p PhysicsTools/NanoAODTools
    rsync -r --stats /scripts/ PhysicsTools/NanoAODTools/. || return 1
    scram b || return 1
    echo "--- Test ST script ---"
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2016preVFP --nleptons 1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2016preVFP.root . || return 1
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2016 --nleptons 1 --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/DYJetsToLL_M-50_2016.root . || return 1
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --nleptons 1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2017.root . || return 1
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2018 --nleptons 1 --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/DYJetsToLL_M-10to50_2018.root . || return 1
}

run_test
