import os
import sys
import math
import json
import ROOT
import random
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaPhi


class JetGenInfo(Module):
    def __init__(self, inputCollection, outputName):
        self.inputCollection = inputCollection
        self.outputName = outputName

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch(self.outputName+"_bPartonCharge","I",lenVar="n"+self.outputName)
        self.out.branch(self.outputName+"_bHadronCharge","I",lenVar="n"+self.outputName)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        jets = self.inputCollection(event)  
        globalJetVars = Collection(event, "global")
        jetoriginVars = Collection(event, "jetorigin")
        
        globalJetIndices = [globalJetVar.jetIdx for globalJetVar in globalJetVars]
        
        bPartonCharge = [0]*len(jets)
        bHadronCharge = [0]*len(jets)
        
        for ijet, jet in enumerate(jets):
            try:
                idx = globalJetIndices.index(jet._index)
            except ValueError:
                print "WARNING: jet (pt: %s, eta: %s) does not have a matching global jet => jet charge cannot be evaluated!" % (jet.pt, jet.eta)
                continue
                

            globalJetVar = globalJetVars[idx]
            jetoriginVar = jetoriginVars[idx]
            if abs(jet.eta - globalJetVar.eta) > 0.01 or \
               abs(deltaPhi(jet.phi,globalJetVar.phi)) > 0.01:
                   print "Warning: jet might be mismatched!"
                   continue
            
            bPartonCharge[ijet] = jetoriginVar.bPartonCharge
            bHadronCharge[ijet] = jetoriginVar.bHadronCharge
            
        self.out.fillBranch(self.outputName+"_bPartonCharge",bPartonCharge)
        self.out.fillBranch(self.outputName+"_bHadronCharge",bHadronCharge)
        
        return True
