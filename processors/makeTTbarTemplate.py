import os
import sys
import math
import argparse
import random
import ROOT
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor \
    import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel \
    import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.modules import *

parser = argparse.ArgumentParser()



parser.add_argument('--year', dest='year',
                    action='store', type=str, default='2016', choices=['2016','2016preVFP','2017','2018'])
parser.add_argument('-i','--input', dest='inputFiles', action='append', default=[])
parser.add_argument('output', nargs=1)

args = parser.parse_args()

print "inputs:",len(args.inputFiles)
print "year:", args.year
print "output directory:", args.output[0]

globalOptions = {
    "isData": False,
    "isSignal": False,
    "year": args.year
}

Module.globalOptions = globalOptions

minMuonPt =     {'2016': 25., '2016preVFP': 25., '2017': 28., '2018': 25.}
minElectronPt = {'2016': 29., '2016preVFP': 29., '2017': 34., '2018': 34.}


met_variable = {
    '2016': lambda event: Object(event, "MET"),
    '2016preVFP': lambda event: Object(event, "MET"),
    '2017': lambda event: Object(event, "MET"), #"METFixEE2017"), #TODO: check if this is still needed for UL
    '2018': lambda event: Object(event, "MET")
}

jesUncertaintyFilesRegrouped = {
    '2016':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/RegroupedV2_Summer19UL16_V7_MC_UncertaintySources_AK4PFchs.txt",
    '2016preVFP': "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/RegroupedV2_Summer19UL16APV_V7_MC_UncertaintySources_AK4PFchs.txt",
    '2017':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/RegroupedV2_Summer19UL17_V5_MC_UncertaintySources_AK4PFchs.txt",
    '2018':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/RegroupedV2_Summer19UL18_V5_MC_UncertaintySources_AK4PFchs.txt"
}
jerResolutionFiles = {
    '2016':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer20UL16_JRV3_MC_PtResolution_AK4PFchs.txt",
    '2016preVFP': "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer20UL16APV_JRV3_MC_PtResolution_AK4PFchs.txt",
    '2017':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer19UL17_JRV2_MC_PtResolution_AK4PFchs.txt",
    '2018':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer19UL18_JRV2_MC_PtResolution_AK4PFchs.txt"
}

jerSFUncertaintyFiles = {
    '2016':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer20UL16_JRV3_MC_SF_AK4PFchs.txt",
    '2016preVFP': "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer20UL16APV_JRV3_MC_SF_AK4PFchs.txt",
    '2017':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer19UL17_JRV2_MC_SF_AK4PFchs.txt",
}

def leptonSequence():
    seq = [
        MuonSelection(
            inputCollection=lambda event: Collection(event, "Muon"),
            outputName="tightMuons",
            storeKinematics=[],
            storeWeights=True,
            muonMinPt=minMuonPt[args.year],
            muonMaxEta=2.4,
            triggerMatch=True,
            muonID=MuonSelection.TIGHT,
            muonIso=MuonSelection.VERYTIGHT,
        ),
        SingleMuonTriggerSelection(
            inputCollection=lambda event: event.tightMuons,
            outputName="IsoMuTrigger",
            storeWeights=True,
        ),
        
        MuonVeto(
            inputCollection=lambda event: event.tightMuons_unselected,
            outputName = "looseMuons",
            muonMinPt = 10.,
            muonMaxEta = 2.4,
        ),

        ElectronSelection(
            inputCollection = lambda event: Collection(event, "Electron"),
            outputName = "tightElectrons",
            electronID = ElectronSelection.WP90,
            electronMinPt = minElectronPt[args.year],
            electronMaxEta = 2.4,
            storeKinematics=[],
            storeWeights=True,
        ),
        SingleElectronTriggerSelection(
            inputCollection=lambda event: event.tightElectrons,
            outputName="IsoElectronTrigger",
            storeWeights=True,
        ),
        ElectronVeto(
            inputCollection=lambda event: event.tightElectrons_unselected,
            outputName = "looseElectrons",
            electronMinPt = 10.,
            electronMaxEta = 2.4,
        ),
        EventSkim(selection=lambda event: (event.IsoMuTrigger_flag > 0) or (event.IsoElectronTrigger_flag > 0)),
        EventSkim(selection=lambda event: (len(event.tightMuons) + len(event.tightElectrons)) == 1),
        EventSkim(selection=lambda event: (len(event.looseMuons) + len(event.looseElectrons)) == 0),
        
    ]
    return seq
    
def jetSelection(jetDict):
    seq = []
    
    btaggedJetCollections = []
    for systName,jetCollection in jetDict.items():
        seq.append(
            JetSelection(
                inputCollection=jetCollection,
                leptonCollectionDRCleaning=lambda event: event.tightMuons+event.tightElectrons,
                jetMinPt=30.,
                jetMaxEta=4.7,
                dRCleaning=0.4,
                jetId=JetSelection.TIGHT,
                outputName="selectedJets_"+systName,
            )
        )
        seq.append(
            BTagSelection(
                inputCollection=lambda event,sys=systName: getattr(event,"selectedJets_"+sys),
                flagName="isBTagged",
                outputName="selectedBJets_"+systName,
                jetMinPt=30.,
                jetMaxEta=2.4,
                workingpoint = BTagSelection.TIGHT,
                storeKinematics=[],
            )
        )
        btaggedJetCollections.append(lambda event, sys=systName: getattr(event,"selectedBJets_"+sys))
        
    systNames = jetDict.keys()
    seq.append(
        EventSkim(selection=lambda event, systNames=systNames: 
            any([getattr(event, "nselectedJets_"+systName) >= 4 for systName in systNames])
        )
    )

    return seq
    
    
def eventReconstruction(uncertaintyDict):
    seq = []
    for systName,(jetCollection,metObject) in uncertaintyDict.items():
        seq.append(WbosonReconstruction(
            leptonObject = lambda event: (event.tightMuons+event.tightElectrons)[0],
            metObject = metObject,
            outputName='wbosons',
            systName=systName
        ))

        seq.append(TTbarReconstructionTemplate(
            bJetCollection=lambda event: filter(lambda jet: jet.isBTagged,jetCollection(event)),
            lJetCollection=lambda event: filter(lambda jet: not jet.isBTagged,jetCollection(event)),
            leptonObject = lambda event: (event.tightMuons+event.tightElectrons)[0],
            wbosonCollection=lambda event,sys=systName: getattr(event,"wbosons_"+sys),
            metObject=metObject,
            outputFileName="ttbarTemplates.root",
        ))
    
    return seq


analyzerChain = [
    EventSkim(selection=lambda event: event.nTrigObj > 0),
    MetFilter(
        globalOptions=globalOptions,
        outputName="MET_filter"
    ),
]
analyzerChain.extend(leptonSequence())

analyzerChain.append(
    JetMetUncertainties(
        jesUncertaintyFilesRegrouped[args.year],
        jerResolutionFiles[args.year],
        jerSFUncertaintyFiles[args.year],
        jesUncertaintyNames = [], 
        metInput = met_variable[args.year],
        rhoInput = lambda event: event.fixedGridRhoFastjetAll,
        jetCollection = lambda event: Collection(event,"Jet"),
        lowPtJetCollection = lambda event: Collection(event,"CorrT1METJet"),
        genJetCollection = lambda event: Collection(event,"GenJet"),
        muonCollection = lambda event: Collection(event,"Muon"),
        electronCollection = lambda event: Collection(event,"Electron"),
        propagateJER = False,
        outputJetPrefix = 'jets_',
        outputMetPrefix = 'met_',
        jetKeys=['jetId', 'nConstituents','btagDeepFlavB'],
        metKeys = [],
    )
)
analyzerChain.extend(
    jetSelection({
        "nominal": lambda event: event.jets_nominal
    })
)
analyzerChain.extend(
    eventReconstruction({
        "nominal": (lambda event: event.selectedJets_nominal, lambda event: event.met_nominal)
    })
)

p = PostProcessor(
    args.output[0],
    args.inputFiles,
    cut="(nJet>1)&&((nElectron+nMuon)>0)",
    modules=analyzerChain,
    friend=True
)

p.run()

