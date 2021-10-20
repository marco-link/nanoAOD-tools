function run_test()
{
    cd $CMSSW_BASE/src/PhysicsTools/NanoAODTools || return 1
    echo
    echo "==================== 2016preVFP ==============="
    python processors/ST.py --year 2016preVFP --ntags 1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2016preVFP.root . || return 1
    echo
    echo "==================== 2016 ====================="
    python processors/ST.py --year 2016 --ntags 1 --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/DYJetsToLL_M-50_2016.root . || return 1
    echo
    echo "==================== 2017 ====================="
    python processors/ST.py --year 2017 --ntags 1 --isSignal --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/WbjToLNu_4f_2017.root . || return 1
    echo
    echo "==================== 2018 ====================="
    python processors/ST.py --year 2018 --ntags 1 --input=https://github.com/WbWbX/test-files/raw/main/nanox_211005/DYJetsToLL_M-10to50_2018.root . || return 1
    echo "==================== done ====================="
}

run_test
