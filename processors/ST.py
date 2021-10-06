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


parser.add_argument('--isData', dest='isData',
                    action='store_true', default=False)
parser.add_argument('--isSignal', dest='isSignal',
                    action='store_true', default=False)
parser.add_argument('--nosys', dest='nosys',
                    action='store_true', default=False)
parser.add_argument('--notagger', dest='notagger',
                    action='store_true', default=False)
parser.add_argument('--year', dest='year',
                    action='store', type=str, default='2016', choices=['2016','2016preVFP','2017','2018'])
parser.add_argument('--nleptons', dest='nleptons', type=int,
                    default=1, choices=[1,2])
parser.add_argument('--input', dest='inputFiles', action='append', default=[])
parser.add_argument('output', nargs=1)

args = parser.parse_args()

print "isData:",args.isData
print "isSignal:",args.isSignal
print "evaluate systematics:",not args.nosys
print "evaluate tagger:",not args.notagger
print "inputs:",len(args.inputFiles)
print "year:", args.year
print "output directory:", args.output[0]

globalOptions = {
    "isData": args.isData,
    "isSignal": args.isSignal,
    "year": args.year
}

Module.globalOptions = globalOptions

isMC = not args.isData

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
    '2018':       "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/jme/Summer19UL18_JRV2_MC_SF_AK4PFchs.txt"
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
        EventSkim(selection=lambda event: (len(event.tightMuons) + len(event.tightElectrons)) == args.nleptons),
        EventSkim(selection=lambda event: (len(event.looseMuons) + len(event.looseElectrons)) == 0),
        
        CombineLeptons(
            muonCollection = lambda event: event.tightMuons,
            electronCollection = lambda event: event.tightElectrons,
            outputName = "tightLeptons"
        ),
        
        
        
    ]
    return seq
    
def jetSelection(jetDict):
    seq = []
    
    btaggedJetCollections = []
    for systName,jetCollection in jetDict.items():
        seq.append(
            JetSelection(
                inputCollection=jetCollection,
                leptonCollectionDRCleaning=lambda event: event.tightLeptons,
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
                outputBName="selectedBJets_"+systName,
                outputLName="selectedLJets_"+systName,
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
            any([getattr(event, "nselectedJets_"+systName) > 2 for systName in systNames])
        )
    )
    
    seq.append(
        ChargeTagging(
            modelPath = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/frozenModel.pb",
            featureDictFile = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/featureDict.py",
            inputCollections = btaggedJetCollections,
            taggerName = "bChargeTag",
        )
    )
    
    '''
    if isMC:
        seq.append(
            JetGenInfo(
                inputCollection = lambda event: event.nominal_selectedBJets,
                outputName = "nominal_selectedBJets",
            )
        )
    '''
    
            
    return seq
    
    
def eventReconstruction(uncertaintyDict):
    seq = []
    for systName,(ljetCollection,bjetCollection,metObject) in uncertaintyDict.items():
        if args.nleptons==1:
            #TODO: outputs are named wrong
            WbosonReconstruction(
                leptonObject = lambda event: event.tightLeptons[0],
                metObject = metObject,
                outputName=systName,
            ),
            TopReconstruction(
                bJetCollection=bjetCollection,
                lJetCollection=ljetCollection,
                leptonObject=lambda event: event.tightLeptons[0],
                wbosonCollection=lambda event,sys=systName: getattr(event,systName+"_w_candidates"),
                metObject = metObject,
                outputName=systName,
            ),
            #TODO: does not yet work with uncertainties
            #XGBEvaluation(
            #    modelPath="${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/bdt/testBDT_bdt.bin",
            #    inputFeatures="${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/bdt/bdt_inputs.py",
            #)
        else:
            pass
    
    return seq


analyzerChain = [
    EventSkim(selection=lambda event: event.nTrigObj > 0),
    MetFilter(
        globalOptions=globalOptions,
        outputName="MET_filter"
    ),
]
analyzerChain.extend(leptonSequence())

if args.isData:
    analyzerChain.extend(
        jetSelection({
            "nominal": lambda event: Collection(event,"Jet")
        })
    )
    analyzerChain.extend(
        eventReconstruction({
            "nominal": (lambda event: Collection(event,"Jet"),met_variable[args.year])
        })
    )

else:
    jesUncertaintyNames = ["Total","Absolute","EC2","BBEC1", "HF","RelativeBal","FlavorQCD" ]
    for jesUncertaintyExtra in ["RelativeSample","HF","Absolute","EC2","BBEC1"]:
        jesUncertaintyNames.append(jesUncertaintyExtra+"_"+args.year.replace("preVFP",""))
    print "JECs: ",jesUncertaintyNames

    analyzerChain.append(
        JetMetUncertainties(
            jesUncertaintyFilesRegrouped[args.year],
            jerResolutionFiles[args.year],
            jerSFUncertaintyFiles[args.year],
            jesUncertaintyNames = jesUncertaintyNames, 
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

    jetDict = {
        "nominal": lambda event: event.jets_nominal,
        "jerUp": lambda event: event.jets_jerUp,
        "jerDown": lambda event: event.jets_jerDown,
    }
    for jesUncertaintyName in jesUncertaintyNames:
        jetDict['jes'+jesUncertaintyName+"Up"] = lambda event,sys=jesUncertaintyName: getattr(event,"jets_jes"+sys+"Up")
        jetDict['jes'+jesUncertaintyName+"Down"] = lambda event,sys=jesUncertaintyName: getattr(event,"jets_jes"+sys+"Down")

    analyzerChain.extend(
        jetSelection(jetDict)
    )

    uncertaintyDict = {
        "nominal": (lambda event: event.selectedLJets_nominal,lambda event: event.selectedBJets_nominal,lambda event: event.met_nominal),
        "jerUp": (lambda event: event.selectedLJets_jerUp,lambda event: event.selectedBJets_jerUp,lambda event: event.met_jerUp),
        "jerDown": (lambda event: event.selectedLJets_jerDown,lambda event: event.selectedBJets_jerDown,lambda event: event.met_jerDown),
    }
    #TODO: add all uncs
    analyzerChain.extend(
        eventReconstruction(uncertaintyDict)
    )

    


if args.isSignal:
    analyzerChain.append(
        ParticleLevel()
    )
    analyzerChain.append(
        PartonLevel()
    )

storeVariables = [
    [lambda tree: tree.branch("PV_npvs", "I"), lambda tree,
     event: tree.fillBranch("PV_npvs", event.PV_npvs)],
    [lambda tree: tree.branch("PV_npvsGood", "I"), lambda tree,
     event: tree.fillBranch("PV_npvsGood", event.PV_npvsGood)],
    [lambda tree: tree.branch("fixedGridRhoFastjetAll", "F"), lambda tree,
     event: tree.fillBranch("fixedGridRhoFastjetAll",
                            event.fixedGridRhoFastjetAll)],
]


if not globalOptions["isData"]:
    storeVariables.append([lambda tree: tree.branch("genweight", "F"),
                           lambda tree,
                           event: tree.fillBranch("genweight",
                           event.Generator_weight)])

    if args.isSignal:
        for coupling in range(1,106):
            storeVariables.append([
                lambda tree, coupling=coupling: tree.branch('LHEWeights_width_%i'%coupling,'F'),
                lambda tree, event, coupling=coupling: tree.fillBranch('LHEWeights_width_%i'%coupling,getattr(event,"LHEWeights_width_%i"%coupling)),
            ])
            
    analyzerChain.append(EventInfo(storeVariables=storeVariables))

p = PostProcessor(
    args.output[0],
    args.inputFiles,
    cut="(nJet>1)&&((nElectron+nMuon)>0)",
    modules=analyzerChain,
    friend=True
)

p.run()

