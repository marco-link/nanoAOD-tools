import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaR, deltaPhi


class BTagSelection(Module):
    #tight DeepFlav WP (https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy)
    LOOSE=0
    MEDIUM=1
    TIGHT=2
    
    def __init__(
        self,
        inputCollection=lambda event: Collection(event, "Jet"),
        outputBName="selectedBJets",
        outputLName="selectedLJets",
        jetMinPt=30.,
        jetMaxEta=2.4,
        workingpoint = TIGHT,
        storeKinematics=['pt', 'eta'],
    ):
        self.inputCollection = inputCollection
        self.outputBName = outputBName
        self.outputLName = outputLName
        self.jetMinPt = jetMinPt
        self.jetMaxEta = jetMaxEta
        self.storeKinematics = storeKinematics
        self.workingpoint = workingpoint
        
        #DONE - but also available in files
        wpValues = {
            '2016preVPF': [0.0614, 0.3093, 0.7221], #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation2016Legacy
            '2016': [0.0480, 0.2489, 0.6377], #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation106XUL16postVFP
            '2017': [0.0532, 0.3040, 0.7476], #https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation106XUL17
            '2018': [0.0490, 0.2783, 0.7100] #https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation106XUL18
        }
        
        if workingpoint==BTagSelection.TIGHT:
            self.taggerFct = lambda jet: jet.btagDeepFlavB>wpValues[Module.globalOptions['year']][2]
        elif workingpoint==BTagSelection.MEDIUM:
            self.taggerFct = lambda jet: jet.btagDeepFlavB>wpValues[Module.globalOptions['year']][1]
        elif workingpoint==BTagSelection.LOOSE:
            self.taggerFct = lambda jet: jet.btagDeepFlavB>wpValues[Module.globalOptions['year']][0]
        else:
            raise Exception("Btagging workingpoint not defined")
            
    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        
        self.out.branch("n"+self.outputBName, "I")
        for variable in self.storeKinematics:
            self.out.branch(self.outputBName+"_"+variable, "F", lenVar="n"+self.outputBName)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        jets = self.inputCollection(event)


        selectedJets = []
        unselectedJets = []


        for jet in jets:
            if jet.pt<self.jetMinPt:
                unselectedJets.append(jet)
                continue
        
            if math.fabs(jet.eta) > self.jetMaxEta:
                unselectedJets.append(jet)
                continue

            if not self.taggerFct(jet):
                unselectedJets.append(jet)
                continue
               
            selectedJets.append(jet)

        self.out.fillBranch("n"+self.outputBName, len(selectedJets))
        for variable in self.storeKinematics:
            self.out.fillBranch(self.outputBName+"_"+variable,
                                map(lambda jet: getattr(jet, variable), selectedJets))

        setattr(event, self.outputBName, selectedJets)
        setattr(event, self.outputLName, unselectedJets)

        return True

