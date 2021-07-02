
import os

# this will use CRAB client API
from CRABAPI.RawCommand import crabCommand

from WMCore.Configuration import Configuration
from CRABClient.UserUtilities import config, getUsernameFromCRIC


year=2016
signalsamples = ['ST_4f_w_lo']



config = Configuration()

config.section_("General")
config.General.workArea = 'crab_{}'.format(year)
config.General.transferOutputs = True


config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.scriptExe = 'crab_script.sh'
config.JobType.inputFiles = ['../processors/WbWbX.py', '../processors/WbWbX_filter.txt', '../scripts/haddnano.py']
config.JobType.sendPythonFolder = True
config.JobType.maxMemoryMB = 2500
#config.JobType.numCores = 1
#config.JobType.sendExternalFolder = True


config.section_("Data")
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.Data.publication = False
config.Data.outLFNDirBase = '/store/user/mlink/WbFriends/v1/{}/'.format(year)
##config.Data.totalUnits = 2


config.section_("Site")
config.Site.storageSite = 'T1_DE_KIT_Disk'


config.section_("User")
config.User.voGroup = 'dcms'
config.JobType.outputFiles = ['tree.root']



# generate samples list
os.system('dasgoclient --query="dataset status=VALID* dataset=/*/*mlink*ChargeRecov2*/USER instance=prod/phys03" > samples.txt')



with open('samples.txt', 'r') as samples:
    for sample in samples:
        sample = sample.rstrip()
        print(sample)

        requestName = sample.split('/')[1]

        if 'ext' in sample:
            requestName = requestName + '_' + sample.split('/')[2].split('_')[-1]

        config.General.requestName = requestName
        config.Data.inputDataset = sample


        arguments = ['year={}'.format(year)]

        if requestName in signalsamples:
            arguments.append('isSignal=1')

        config.JobType.scriptArgs = arguments


        # save config
        with open('{}_{}.py'.format(year, requestName), 'w') as f:
            print >> f, config


        logpath = 'crab_{y}/crab_{proc}'.format(y=year, proc=requestName)
        if os.path.isdir(logpath):
            print('Already submitted (see "{}"). Skipping!\n'.format(logpath))
        else:
            print('submitting {} ...'.format(requestName))
            result = crabCommand('submit', config = config)
            print (result)


os.system('rm samples.txt')
