import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class ElectronVeto(Module):

    def __init__(
        self,
        inputCollection = lambda event: Collection(event, "Electron"),
        outputName = "vetoElectrons",
        electronMinPt = 10.,
        electronMaxEta = 2.4,
    ):
        self.inputCollection = inputCollection
        self.outputName = outputName
        self.electronMinPt = electronMinPt
        self.electronMaxEta = electronMaxEta
 
    def beginJob(self):
        pass
        
    def endJob(self):
        pass
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        #self.out.branch("n"+self.outputName,"I")
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
        
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        electrons = self.inputCollection(event)
        
        selectedElectrons = []
        unselectedElectrons = []
        
        #use electron cut-based veto ID
        for electron in electrons:
            if electron.pt>self.electronMinPt and math.fabs(electron.eta)<self.electronMaxEta and electron.cutBased>=1:
                selectedElectrons.append(electron)
            else:
                unselectedElectrons.append(electron)
  
        #self.out.fillBranch("n"+self.outputName,len(selectedElectrons))
        
        setattr(event,self.outputName,selectedElectrons)
        setattr(event,self.outputName+"_unselected",unselectedElectrons)

        return True
        
