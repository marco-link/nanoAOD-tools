import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class CombineLeptons(Module):
    def __init__(self,
        muonCollection = lambda event: Collection(event,"Muon"),
        electronCollection = lambda event: Collection(event,"Electron"),
        outputName = "leptons",
        storeKinematics = []
    ):
        self.muonCollection = muonCollection
        self.electronCollection = electronCollection
        self.outputName=outputName
        self.storeKinematics=storeKinematics

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch("n"+self.outputName, "I")
        for variable in self.storeKinematics:
            self.out.branch(self.outputName+"_"+variable,"F",lenVar="n"+self.outputName)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        leptons = []
        
        for muon in self.muonCollection(event):
            muon.isMuon = True
            muon.isElectron = False
            muon.relIso = muon.pfRelIso04_all
            leptons.append(muon)
        for electron in self.electronCollection(event):
            electron.isMuon = False
            electron.isElectron = True
            electron.relIso = electron.pfRelIso03_all
            leptons.append(electron)
            
        leptons = list(reversed(sorted(leptons,key=lambda x: x.pt)))
        
        self.out.fillBranch("n"+self.outputName,len(leptons))
        for variable in self.storeKinematics:
            self.out.fillBranch(self.outputName+"_"+variable,map(lambda lepton: getattr(lepton,variable), leptons))
            
            
        setattr(event,self.outputName,leptons)
            
        return True
            
            
