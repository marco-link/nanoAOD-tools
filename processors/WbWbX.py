import os
import sys
import math
import argparse
import random
import ROOT
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.modules import *

parser = argparse.ArgumentParser()

parser.add_argument('--isData', dest='isData', action='store_true', default=False)
parser.add_argument('--isSignal', dest='isSignal', action='store_true', default=False)
parser.add_argument('--year', dest='year', action='store', type=int, default=2016)
parser.add_argument('--input', dest='inputFiles', action='append', default=[])
parser.add_argument('--maxEntries', '-N', type=int, default=None)
parser.add_argument('output', nargs=1)
parser.add_argument('--step', type=int, default=0, help='stepnumber of the analysis workflow to run (can only run one step at a time)')


args = parser.parse_args()
print(args)

globalOptions = {
    "isData": args.isData,
    "isSignal": args.isSignal,
    "year": args.year
}

isMC = not args.isData


preskim = {
            2016: '(HLT_IsoMu24 == 1) || (HLT_IsoTkMu24 == 1) || (HLT_Ele32_eta2p1_WPTight_Gsf==1)',
            2017: '(HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned == 1) || (HLT_Ele35_WPTight_Gsf == 1) || (HLT_IsoMu27==1)',
            2018: '(HLT_IsoMu24 == 1) || (HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned == 1) || (HLT_Ele32_WPTight_Gsf == 1)'
          }



leptonselection = 'nElectron + nMuon == 1' # applied before step 2
def WNonB_mass(event):
    jet = Collection(event, 'NonBJet')

    if len(jet)>0:
        return (Object(event, 'Reco_w').p4() + jet[0].p4()).M()
    else:
        return -1


# applied before step 3
selections = ['(nBJet == 1 || (nBJet == 2 && BJet_pt[1] < 50))',
              '(nNonBJet == 1 || (nNonBJet == 2 && NonBJet_pt[1] < 50))',
              'abs(BJet_eta[0]) < 2.5 && BJet_pt[0] > 25',
              'abs(NonBJet_eta[0]) > 2.3',
              'WNonB_mass > 140',
              'Reco_w_pt < 120 && abs(Reco_w_eta) < 4.0',
             ]
selection = ' && '.join(selections)











# TODO verify WPs
looseWP = {
            2016: 0.06140,
            2017: 0.05210,
            2018: 0.04940
          }

mediumWP = {
            2016: 0.30930,
            2017: 0.30330,
            2018: 0.27700
           }

tightWP = {
            2016: 0.72210,
            2017: 0.74890,
            2018: 0.72640
          }


# used for onshell/offshell
topmass = 172.5
masswindow = 20







##############
##  STEP 1  ##
##############


# apply preskim only to background
preskimcut = ''
if not args.isSignal:
    preskimcut = preskim[args.year]



step1_analyzerChain = [

#TODO particle selections/filters

    #MuonSelection(
        #inputCollection=lambda event: Collection(event, "Muon"),
        #outputName="tightMuons",
        #storeKinematics=['pt','eta'],
        #storeWeights=True,
        #muonMinPt=minMuonPt[globalOptions["year"]],
        #triggerMatch=True,
        #muonID=MuonSelection.TIGHT,
        #muonIso=MuonSelection.TIGHT,
        #globalOptions=globalOptions
    #),

    #EventSkim(selection=lambda event: event.ntightMuons > 0),
    #SingleMuonTriggerSelection(
        #inputCollection=lambda event: event.tightMuons,
        #outputName="IsoMuTrigger",
        #storeWeights=True,
        #globalOptions=globalOptions
    #),

    #EventSkim(selection=lambda event: event.IsoMuTrigger_flag > 0),
    #MuonVeto(
        #inputCollection=lambda event: event.tightMuons_unselected,
        #outputName = "vetoMuons",
        #muonMinPt = 10.,
        #muonMaxEta = 2.4,
        #globalOptions=globalOptions
    #),
    #MetFilter(
        #globalOptions=globalOptions,
        #outputName="MET_filter"
    #),
    #JetSelection(
        #inputCollection=lambda event: Collection(event,"Jet"),
        ##leptonCollectionDRCleaning=lambda event: event.tightMuons,
        #jetMinPt=30.,
        #jetMaxEta=4.7,
        #jetId=JetSelection.LOOSE,
        #outputName="selectedJets",
        #storeKinematics=['pt','eta', 'phi'],
        #globalOptions=globalOptions
    #),




#TODO weights calculation

#TODO scale factor calculation


    # Jet charge from partonFlavor #TODO switch to selectedJets
    JetGenChargeProducer(
                        ),
]

# add Wb generator to signal sample
if args.isSignal:
    step1_analyzerChain.append(WbGenProducer(dRmax=0.4))



step1 = PostProcessor(
    args.output[0],
    args.inputFiles,
    postfix='_1',
    cut=preskimcut,
    modules=step1_analyzerChain,
    friend=False,
    outputbranchsel='processors/step1.txt',
    maxEntries=args.maxEntries,
)




##############
##  STEP 2  ##
##############

step2_analyzerChain = [
    # leptonic W reco
    WbosonReconstruction(electronCollectionName = 'Electron',
                         muonCollectionName = 'Muon',
                         metName = 'MET',
                         outputName='Reco_w',
                         Wmass = 80.385
                         ),


# TODO apply b charge tagger

    # apply btagging WP
    TagJetProducer(JetCollectionName = 'Jet',
                   TagJetOutputName = 'BJet',
                   NonTagJetOutputName = 'NonBJet',
                   storeVariables = ['mass', 'pt', 'eta', 'phi', 'btagDeepFlavB', 'GenCharge'],  #TODO add b charge tagger charge
                   tagger = 'btagDeepFlavB',
                   WP = mediumWP[args.year])

    CalcVar(
        function = WNonB_mass,
        outputName = 'WNonB_mass',
        vartype='F'
    ),
]



step2 = PostProcessor(
    args.output[0],
    args.inputFiles,
    postfix='_2',
    cut=leptonselection,
    modules=step2_analyzerChain,
    friend=False,
    outputbranchsel='processors/step2.txt',
    maxEntries=args.maxEntries,
)




##############
##  STEP 3  ##
##############



step3_analyzerChain = [

    # Wb reco
    WbReconstruction(
        bjetCollectionName = 'BJet',
        WbosonCollectionName = 'Reco_w',
        jetchargeName='GenCharge', #TODO replace with charge from b charge tagger
        outputName='Reco_wb'
    ),

    # apply binning for asymmetry
    AsymBinProducer(
        massBranch='Reco_wb_mass',
        chargeBranch='Reco_wb_bjet_charge',
        outputName='Reco_AsymBin',
        mass=topmass,
        masswindow=masswindow
    ),
]

# generator distributions
if args.isSignal:
    # add smeared truth charge
    step3_analyzerChain.append(ChargeSmearProducer(
                                    chargeBranch='Gen_wb_b_Charge',
                                    efficiency=0.66
                                ))

    # calculate asymmetry for (smeared) generator truth
    step3_analyzerChain.append(AsymBinProducer(
                                    massBranch='Gen_wb_mass',
                                    chargeBranch='Gen_wb_b_Charge',
                                    outputName='Reco_GenAsymBin',
                                    mass=topmass,
                                    masswindow=masswindow
                               ))
    step3_analyzerChain.append(AsymBinProducer(
                                    massBranch='Gen_wb_mass',
                                    chargeBranch='Gen_wb_b_Charge_smeared',
                                    outputName='Reco_smearedGenAsymBin',
                                    mass=topmass,
                                    masswindow=masswindow
                               ))







step3 = PostProcessor(
    args.output[0],
    args.inputFiles,
    postfix='_3',
    cut=selection,
    modules=step3_analyzerChain,
    friend=False,
    outputbranchsel='processors/step3.txt',
    maxEntries=args.maxEntries,
)





# Run analysis

if args.step == 0:
    print('Nothing todo. Take a break!')
elif args.step == 1:
    step1.run()
elif args.step == 2:
    step2.run()
elif args.step == 3:
    step3.run()
else:
    print('Step not specified. Mismatch!')
