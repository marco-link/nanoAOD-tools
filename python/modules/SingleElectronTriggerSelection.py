import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import getHist,combineHist2D,getSFXY

class SingleElectronTriggerSelection(Module):
    def __init__(
        self,
        inputCollection = lambda event: getattr(event,"tightElectron"),
        storeWeights=False,
        outputName = "IsoElectronTrigger",
        doVariations = True
    ):
        self.inputCollection = inputCollection
        self.outputName = outputName
        self.storeWeights = storeWeights
        self.doVariations = doVariations


        if not self.globalOptions["isData"]:
            if self.globalOptions["year"] == '2016' or self.globalOptions["year"] == '2016preVFP':

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/electrons/trigger/Efficiencies_electron_DL_Run2016BCDEFGH_UL_SingleElectronTrigger.root",
                    "NUM_Ele27_WPTight_DEN_MVA90Id_eta_pt_syst"
                )

            elif self.globalOptions["year"] == '2017':

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/electrons/trigger/Efficiencies_electron_DL_Run2017BCDEF_UL_SingleElectronTrigger.root",
                    "NUM_Ele32_WPTight_L1DoubleEG_DEN_MVA90Id_eta_pt_syst"
                )
   
            elif self.globalOptions["year"] == '2018':

                self.triggerSFHist = getHist(
                    "PhysicsTools/NanoAODTools/data/electrons/trigger/Efficiencies_electron_DL_Run2018ABCD_UL_SingleElectronTrigger.root",
                    "NUM_Ele32_WPTight_DEN_MVA90Id_eta_pt_syst"
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
        
        if not Module.globalOptions["isData"] and self.storeWeights:
            self.out.branch(self.outputName+"_weight_trigger_{}_nominal".format(Module.globalOptions['year'].replace('preVFP','')),"F")
            if self.doVariations:
                self.out.branch(self.outputName+"_weight_trigger_{}_up".format(Module.globalOptions['year'].replace('preVFP','')),"F")
                self.out.branch(self.outputName+"_weight_trigger_{}_down".format(Module.globalOptions['year'].replace('preVFP','')),"F")
            
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
        
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        electrons = self.inputCollection(event)
        
        weight_trigger_nominal = 1.
        if self.doVariations:
            weight_trigger_up = 1.
            weight_trigger_down = 1.
        

        if (not self.globalOptions["isData"]) and len(electrons)>0 and self.storeWeights: 
            weight_trigger,weight_trigger_err = getSFXY(self.triggerSFHist,electrons[0].pt,electrons[0].eta)
            weight_trigger_nominal*=weight_trigger
            if self.doVariation:
                weight_trigger_up*=(weight_trigger+weight_trigger_err)
                weight_trigger_down*=(weight_trigger-weight_trigger_err)


        trigger_flag = 0

        if Module.globalOptions["year"] == '2016' or Module.globalOptions["year"] == '2016preVFP':
            trigger_flag = event.HLT_Ele27_WPTight_Gsf

        elif Module.globalOptions["year"] == '2017':
            trigger_flag = event.HLT_Ele32_WPTight_Gsf_L1DoubleEG

        elif Module.globalOptions["year"] == '2018':
            trigger_flag = event.HLT_Ele32_WPTight_Gsf

        self.out.fillBranch(self.outputName+"_flag", trigger_flag)
            
        if not Module.globalOptions["isData"] and self.storeWeights:
            self.out.fillBranch(self.outputName+"_weight_trigger_{}_nominal".format(Module.globalOptions['year'].replace('preVFP','')),weight_trigger_nominal)
            if self.doVariations:
                self.out.fillBranch(self.outputName+"_weight_trigger_{}_up".format(Module.globalOptions['year'].replace('preVFP','')),weight_trigger_up)
                self.out.fillBranch(self.outputName+"_weight_trigger_{}_down".format(Module.globalOptions['year'].replace('preVFP','')),weight_trigger_down)

        return True
        
