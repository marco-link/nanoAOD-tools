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
parser.add_argument('--year', dest='year',
                    action='store', type=int, default=2016)
parser.add_argument('--input', dest='inputFiles', action='append', default=[])
parser.add_argument('output', nargs=1)

args = parser.parse_args()

print "isData:",args.isData
print "isSignal:",args.isSignal
print "inputs:",len(args.inputFiles)
print "year:", args.year
print "output directory:", args.output[0]

globalOptions = {
    "isData": args.isData,
    "isSignal": args.isSignal,
    "year": args.year
}

isMC = not args.isData

minMuonPt = {2016: 25., 2017: 28., 2018: 25.}
minElectronPt = {2016: 29., 2017: 34., 2018: 34.}


met_variable = {
    2016: lambda event: Object(event, "MET"),
    2017: lambda event: Object(event, "METFixEE2017"),
    2018: lambda event: Object(event, "MET")
}


analyzerChain = [
    EventSkim(selection=lambda event: event.nTrigObj > 0),
    MuonSelection(
        inputCollection=lambda event: Collection(event, "Muon"),
        outputName="tightMuons",
        storeKinematics=['pt','eta','charge'],
        storeWeights=True,
        muonMinPt=minMuonPt[globalOptions["year"]],
        triggerMatch=True,
        muonID=MuonSelection.TIGHT,
        muonIso=MuonSelection.TIGHT,
        globalOptions=globalOptions
    ),
    
    EventSkim(selection=lambda event: event.ntightMuons == 1),
    SingleMuonTriggerSelection(
        inputCollection=lambda event: event.tightMuons,
        outputName="IsoMuTrigger",
        storeWeights=True,
        globalOptions=globalOptions
    ),
    
    EventSkim(selection=lambda event: event.IsoMuTrigger_flag > 0),
    MuonVeto(
        inputCollection=lambda event: event.tightMuons_unselected,
        outputName = "vetoMuons",
        muonMinPt = 10.,
        muonMaxEta = 2.4,
        globalOptions=globalOptions
    ),
    EventSkim(selection=lambda event: event.nvetoMuons == 0),
    MetFilter(
        globalOptions=globalOptions,
        outputName="MET_filter"
    ),
    JetSelection(
        inputCollection=lambda event: Collection(event,"Jet"),
        leptonCollectionDRCleaning=lambda event: event.tightMuons,
        jetMinPt=30.,
        jetMaxEta=4.7,
        jetId=JetSelection.LOOSE,
        outputName="nominal_selectedJets",
        globalOptions=globalOptions
    ),
    BTagSelection(
        inputCollection=lambda event: event.nominal_selectedJets,
        outputName="nominal_selectedBJets",
        jetMinPt=30.,
        jetMaxEta=2.4,
    ),
    EventSkim(selection=lambda event: event.nnominal_selectedJets>=2 and event.nnominal_selectedBJets==1),
    JetGenInfo(
        inputCollection = lambda event: event.nominal_selectedBJets,
        outputName = "nominal_selectedBJets",
        globalOptions=globalOptions
    ),
    ChargeTagging(
        modelPath = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/frozenModel.pb",
        featureDictFile = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/featureDict.py",
        inputCollections = [lambda event: event.nominal_selectedBJets],
        taggerName = "tagger",
    ),
    SimpleJetChargeSum(
        inputCollection=lambda event: event.nominal_selectedBJets,
        outputCollection="selectedBJets",
        outputName="betaChargeSum",
        beta=0.8,
        globalOptions=globalOptions
    ),
    WbosonReconstruction(
        leptonObject = lambda event: event.tightMuons[0],
        metObject =lambda event: Object(event, "MET"),
        outputName="nominal",
    ),
    TopReconstruction(
        bJetCollection=lambda event: event.nominal_selectedBJets,
        lJetCollection=lambda event: event.nominal_selectedBJets_unselected,
        leptonObject=lambda event: event.tightMuons[0],
        wbosonCollection=lambda event: event.nominal_w_candidates,
        metObject = lambda event: Object(event, "MET"),
        outputName="nominal",
        globalOptions=globalOptions
    )
    
    
]



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
    cut="(nJet>0)&&((nElectron+nMuon)>0)",
    modules=analyzerChain,
    friend=True
)

p.run()

