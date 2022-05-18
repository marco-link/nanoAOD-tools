import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import getHist,combineHist2D,getSFXY

class SingleMuonTriggerSelection(Module):
    def __init__(
        self,
        inputCollection = lambda event: getattr(event,"tightMuons"),
        storeWeights=True,
        outputName = "IsoMuTrigger",
        doVariations = True
    ):
        self.inputCollection = inputCollection
        self.outputName = outputName
        self.storeWeights = storeWeights
        self.doVariations = doVariations

        if not Module.globalOptions["isData"]:
            if Module.globalOptions["year"] == '2016':

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2016postVFP_UL/NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt.root",
                    "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt_syst"
                )

            elif Module.globalOptions["year"] == '2016preVFP':

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2016preVFP_UL/NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt.root",
                    "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt_syst"
                )

            elif Module.globalOptions["year"] == '2017':

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2017_UL/NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt.root",
                    "NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt_syst"
                )
   
            elif Module.globalOptions["year"] == '2018':

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2018_UL/NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt.root",
                    "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoVeryTight_abseta_pt_syst"
                )
            else: 
                print("Invalid year")
                sys.exit(1)
            
            
    def beginJob(self):
        pass
        
    def endJob(self):
        pass
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        
        self.out.branch(self.outputName+"_flag","I")
        
        if not self.globalOptions["isData"] and self.storeWeights:
            self.out.branch(self.outputName+"_weight_trigger_{}_nominal".format(Module.globalOptions['year'].replace('preVFP','')),"F")
            if self.doVariations:
                self.out.branch(self.outputName+"_weight_trigger_{}_up".format(Module.globalOptions['year'].replace('preVFP','')),"F")
                self.out.branch(self.outputName+"_weight_trigger_{}_down".format(Module.globalOptions['year'].replace('preVFP','')),"F")
            
            
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
        
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        muons = self.inputCollection(event)
        
        weight_trigger_nominal = 1.
        if self.doVariations:
            weight_trigger_up = 1.
            weight_trigger_down = 1.
        
        if (not Module.globalOptions["isData"]) and len(muons)>0 and self.storeWeights: 
            weight_trigger,weight_trigger_err = getSFXY(self.triggerSFHist,abs(muons[0].eta),muons[0].pt)
            weight_trigger_nominal*=weight_trigger
            if self.doVariations:
                weight_trigger_up*=(weight_trigger+weight_trigger_err)
                weight_trigger_down*=(weight_trigger-weight_trigger_err)

        trigger_flag = 0

        if Module.globalOptions["year"] == '2016' or Module.globalOptions["year"] == '2016preVFP':
            trigger_flag = event.HLT_IsoMu24>0 or event.HLT_IsoTkMu24>0

        elif Module.globalOptions["year"] == '2017':
            trigger_flag = event.HLT_IsoMu27>0

        elif Module.globalOptions["year"] == '2018':
            trigger_flag = event.HLT_IsoMu24

        self.out.fillBranch(self.outputName+"_flag", trigger_flag)
            
        if not Module.globalOptions["isData"] and self.storeWeights:
            self.out.fillBranch(self.outputName+"_weight_trigger_{}_nominal".format(Module.globalOptions['year'].replace('preVFP','')),weight_trigger_nominal)
            if self.doVariations:
                self.out.fillBranch(self.outputName+"_weight_trigger_{}_up".format(Module.globalOptions['year'].replace('preVFP','')),weight_trigger_up)
                self.out.fillBranch(self.outputName+"_weight_trigger_{}_down".format(Module.globalOptions['year'].replace('preVFP','')),weight_trigger_down)

        return True
        
