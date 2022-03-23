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
    echo "==================== 2017 (ntags=-1) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags -1 --isSignal --maxEvents 1000 --input=/afs/cern.ch/user/m/mdefranc/work/public/WbWbX/mc_2017_2022-03-01_v6/WbjToLNu_4f_2017.root . || return 1
    echo
    echo "==================== 2017 (ntags=1) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags 1 --isSignal --maxEvents 1000 --input=/afs/cern.ch/user/m/mdefranc/work/public/WbWbX/mc_2017_2022-03-01_v6/WbjToLNu_4f_2017.root . || return 1
    echo
    echo "==================== 2017 (ntags=2) ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags 2 --isSignal --maxEvents 1000 --input=/afs/cern.ch/user/m/mdefranc/work/public/WbWbX/mc_2017_2022-03-01_v6/WbjToLNu_4f_2017.root . || return 1
    
    echo "==================== 2017 TT semileptonic ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags -1 --maxEvents 1000 --input=/afs/cern.ch/user/m/mdefranc/work/public/WbWbX/mc_2017_2022-03-01_v6/TTToSemiLeptonic_2017.root . || return 1

    echo "==================== 2017 ST leptonic ====================="
    python PhysicsTools/NanoAODTools/processors/ST.py --year 2017 --ntags -1 --maxEvents 1000 --input=/afs/cern.ch/user/m/mdefranc/work/public/WbWbX/mc_2017_2022-03-01_v6/ST_s-channel_4f_leptonDecays_2017.root . || return 1

    

    echo "==================== done ====================="
}

run_test
