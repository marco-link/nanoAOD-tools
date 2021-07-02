#this is not mean to be run locally
#

# ls -lR .
# echo "ENV..................................."
# env

echo "VOMS"
voms-proxy-info -all

echo "CMSSW BASE, python path, pwd"
echo $CMSSW_BASE
echo $PYTHON_PATH
echo $PWD

echo Found Proxy in: $X509_USER_PROXY

for i in "$@"; do
    case $i in
        year=*)
        opt_year="${i#*=}"
        ;;
        isSignal=1)
        opt_issignal="--isSignal"
        ;;
        isData=1)
        opt_isdata="--isData"
        ;;
    esac
done

echo $opt_year
echo $opt_issignal
echo $opt_isdata


echo "---> python WbWbX.py"
python WbWbX.py --crab --year $opt_year $opt_issignal $opt_isdata
echo "DONE with crab_script.sh"
ls -l
