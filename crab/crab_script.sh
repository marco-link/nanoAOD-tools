#this is not meant to be run locally
#

echo "+++ crab_script.sh +++"
if [ "`tty`" != "not a tty" ]; then
    echo "YOU SHOULD NOT RUN THIS IN INTERACTIVE, IT DELETES YOUR LOCAL FILES"
else
#     ls -lR .
    ls -l
    echo "ENV..................................."
    env
    echo "VOMS..................................."
    voms-proxy-info -all
    echo "CMSSW BASE, python path, pwd"
    echo $CMSSW_BASE
    echo $PYTHON_PATH
    echo $PWD
    # rm -rf $CMSSW_BASE/lib/
    # rm -rf $CMSSW_BASE/src/
    # rm -rf $CMSSW_BASE/module/
    # rm -rf $CMSSW_BASE/python/
    # mv lib $CMSSW_BASE/lib
    # mv src $CMSSW_BASE/src
    # mv module $CMSSW_BASE/module
    # mv python $CMSSW_BASE/python
    echo Found Proxy in: $X509_USER_PROXY

    echo $@
    for i in "$@"; do
    case $i in
        isSignal=*)
            if [ "${i#*=}" -gt "0" ]; then
                opt_isSignal="--isSignal"
            else
                opt_isSignal=""
            fi
        ;;
        year=*)
            opt_year="${i#*=}"
        ;;
        ntags=*)
            opt_ntags="${i#*=}"
        ;;
    esac
    done

    echo "---> python ST.py"
    python ST.py --crab $opt_isSignal --year $opt_year --ntags $opt_ntags
    ls -lv
    echo "DONE with crab_script.sh"
fi
