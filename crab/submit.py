
import os
import subprocess
import argparse


# this will use CRAB client API
from CRABAPI.RawCommand import crabCommand

from WMCore.Configuration import Configuration
from CRABClient.UserUtilities import config, getUsernameFromCRIC


RED   = "\033[1;31m"
BLUE  = "\033[1;34m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"

years = ['2016preVFP', '2016', '2017', '2018']

parser = argparse.ArgumentParser()

parser.add_argument('--input', '-i', type=str, required=True,
                    help='input txt file containing the sample names (one line each)')

parser.add_argument('--version', '-v', type=str, required=True,
                    help='version tag')

parser.add_argument('--dry', action='store_true',
                    help='only generate configs, don\'t submit the jobs')

parser.add_argument('--data', action='store_true',
                    help='for data processing')


args = parser.parse_args()
print(args)



# Configuration
config = Configuration()

config.section_("General")
config.General.workArea = 'crab_' + args.version
config.General.transferOutputs = True
config.General.transferLogs = True

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.inputFiles = ['../processors/ST.py', '../processors/branchfilter.txt', '../scripts/haddnano.py']
config.JobType.scriptExe = 'crab_script.sh'
config.JobType.maxMemoryMB = 2500
config.JobType.maxJobRuntimeMin = 300
config.JobType.outputFiles = ['nano.root']
config.JobType.sendPythonFolder = True
config.JobType.allowUndistributedCMSSW = True

config.section_("Data")
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.Data.publication = False
##config.Data.totalUnits = 2
config.Data.outputDatasetTag = 'WbNanoAODTools_{}'.format(args.version)
config.Data.allowNonValidInputDataset = False

config.section_("Site")
config.Site.storageSite = 'T1_DE_KIT_Disk'
#config.Site.blacklist = ['T2_US_*']

config.section_("User")
config.User.voGroup = 'dcms'



with open(args.input, 'r') as samplefile:
    for sample in samplefile:
        sample = sample.strip()

        if not '#' in sample and len(sample.split('/')) == 4:
            requestName = sample.split('/')[1]
            print(requestName)

            year = -1
            for y in years:
                if y in sample:
                    year = y
            if year not in years:
                raise Exception('year "{}" not found, available options: {}'.format(year, ', '.join(years)))

            config.General.requestName = requestName
            config.Data.inputDataset = sample
            config.JobType.scriptArgs = ['year={}'.format(year), 'isSignal={}'.format(1 if 'WbjToLNu_4f' in requestName else 0), 'ntags=-1']
            config.Data.outLFNDirBase = '/store/user/mlink/WbNanoAODTools/{}/'.format(args.version)

            # save config
            with open('{}_{}.py'.format(year, requestName), 'w') as f:
                print >> f, config

            if not args.dry:
                logpath = 'crab_{}/crab_{}'.format(args.version, requestName)
                if os.path.isdir(logpath):
                    print('Already submitted (see "{}"). Skipping!'.format(logpath))
                else:
                    print('submitting {} ...'.format(requestName))

                    result = crabCommand('submit', config=config)
                    print (result)
