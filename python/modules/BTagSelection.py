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
    
    def __init__(
         self,
         inputCollection=lambda event: Collection(event, "Jet"),
         outputBName="selectedBJets",
         outputLName="selectedLJets",
         jetMinPt=30.,
         jetMaxEta=2.4,
         storeKinematics=['pt', 'eta'],
         taggerFct = lambda jet: jet.btagDeepFlavB>0.7221,
     ):
        self.inputCollection = inputCollection
        self.outputBName = outputBName
        self.outputLName = outputLName
        self.jetMinPt = jetMinPt
        self.jetMaxEta = jetMaxEta
        self.storeKinematics = storeKinematics
        self.taggerFct = taggerFct

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch("n"+self.outputBName, "I")
        for variable in self.storeKinematics:
            self.out.branch(self.outputBName+"_"+variable, "F", lenVar="n"+self.outputBName)

        self.out.branch("n"+self.outputLName, "I")
        for variable in self.storeKinematics:
            self.out.branch(self.outputLName+"_"+variable, "F", lenVar="n"+self.outputLName)

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

        self.out.fillBranch("n"+self.outputLName, len(unselectedJets))
        for variable in self.storeKinematics:
            self.out.fillBranch(self.outputLName+"_"+variable,
                                map(lambda jet: getattr(jet, variable), unselectedJets))

        setattr(event, self.outputBName, selectedJets)
        setattr(event, self.outputLName, unselectedJets)

        return True
