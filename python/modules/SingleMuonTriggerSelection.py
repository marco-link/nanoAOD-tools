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
        isData=None,
        year=None
    ):
        self.inputCollection = inputCollection
        self.outputName = outputName
        self.storeWeights = storeWeights

        if isData is None:
            raise Exception("SingleMuonTriggerSelection requires argument 'isData'")
        else:
            self.isData=isData

        if year is None:
            raise Exception("SingleMuonTriggerSelection requires argument 'year'")
        else:
            self.year = year

        if not self.isData:
            if self.year == 2016:

                triggerSFBToF = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2016/EfficienciesAndSF_RunBtoF.root",
                    "IsoMu24_OR_IsoTkMu24_PtEtaBins/pt_abseta_ratio"
                )
                triggerSFGToH = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2016/EfficienciesAndSF_RunGtoH.root",
                    "IsoMu24_OR_IsoTkMu24_PtEtaBins/pt_abseta_ratio"
                )
                self.triggerSFHist = combineHist2D(
                    triggerSFBToF,
                    triggerSFGToH,
                    1.-16226.5/35916.4,
                    16226.5/35916.4
                )

            elif self.year == 2017:

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2017/EfficienciesStudies_2017_trigger_EfficienciesAndSF_RunBtoF_Nov17Nov2017.root",
                    "IsoMu27_PtEtaBins/pt_abseta_ratio"
                )
   
            elif self.year == 2018:

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/muon/2018/EfficienciesStudies_2018_trigger_EfficienciesAndSF_2018Data_AfterMuonHLTUpdate.root",
                    "IsoMu24_PtEtaBins/pt_abseta_ratio"
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
        
        if not self.isData and self.storeWeights:
            self.out.branch(self.outputName+"_weight_trigger_nominal","F")
            self.out.branch(self.outputName+"_weight_trigger_up","F")
            self.out.branch(self.outputName+"_weight_trigger_down","F")
            
            
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
        
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        muons = self.inputCollection(event)
        
        weight_trigger_nominal = 1.
        weight_trigger_up = 1.
        weight_trigger_down = 1.
        
        if (not self.isData) and len(muons)>0 and self.storeWeights:
            weight_trigger,weight_trigger_err = getSFXY(self.triggerSFHist,muons[0].pt,abs(muons[0].eta))
            weight_trigger_nominal*=weight_trigger
            weight_trigger_up*=(weight_trigger+weight_trigger_err)
            weight_trigger_down*=(weight_trigger-weight_trigger_err)

        trigger_flag = 0

        if self.year == 2016:
            trigger_flag = event.HLT_IsoMu24>0 or event.HLT_IsoTkMu24>0

        elif self.year == 2017:
            trigger_flag = event.HLT_IsoMu27>0 or event.HLT_IsoMu24>0

        elif self.year == 2018:
            trigger_flag = event.HLT_IsoMu24

        self.out.fillBranch(self.outputName+"_flag", trigger_flag)
            
        if not self.isData and self.storeWeights:
            self.out.fillBranch(self.outputName+"_weight_trigger_nominal",weight_trigger_nominal)
            self.out.fillBranch(self.outputName+"_weight_trigger_up",weight_trigger_up)
            self.out.fillBranch(self.outputName+"_weight_trigger_down",weight_trigger_down)

        return True
        
