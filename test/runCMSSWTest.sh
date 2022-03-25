function run_test()
{
    cd ~
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    export SCRAM_ARCH=slc7_amd64_gcc820 || return 1
    echo
    echo "==================== setup CMSSW ==============="
    scramv1 project CMSSW CMSSW_11_1_7 || return 1
    cd CMSSW_11_1_7/src || return 1
    eval `scram runtime -sh` || return 1
    mkdir -p PhysicsTools/NanoAODTools
    rsync -r --stats /scripts/ PhysicsTools/NanoAODTools/. || return 1
    echo
    echo "==================== compiling ================"
    scram b || return 1
    
    echo
    echo "==================== 2016preVFP (ntags=-1) ==============="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2016preVFP --ntags -1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2016preVFP.root || return 1
    echo
    echo "==================== 2016preVFP (ntags=0) ==============="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2016preVFP --ntags 0 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2016preVFP.root || return 1
    echo
    echo "==================== 2016preVFP (ntags=1) ==============="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2016preVFP --ntags 1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2016preVFP.root || return 1
    echo
    echo "==================== 2016preVFP (ntags=2) ==============="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2016preVFP --ntags 2 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2016preVFP.root || return 1
    
    echo
    echo "==================== 2016 (ntags=0) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2016 --ntags 0 --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/DYJetsToLL_M-50_2016.root || return 1
    
    echo
    echo "==================== 2017 (ntags=-1) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags -1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2017.root || return 1
    echo
    echo "==================== 2017 (ntags=1) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags 1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2017.root || return 1
    echo
    echo "==================== 2017 (ntags=2) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags 2 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2017.root || return 1
    
    echo
    echo "==================== 2018 (ntags=-1) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2018 --ntags -1 --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/DYJetsToLL_M-10to50_2018.root || return 1
    echo
    echo "==================== 2018 (ntags=0) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2018 --ntags 0 --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/DYJetsToLL_M-10to50_2018.root || return 1
    
    echo "==================== done ====================="
}

run_test
