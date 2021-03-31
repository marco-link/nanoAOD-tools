import os
import sys
import math
import json
import ROOT
import random
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaR, deltaPhi


class SimpleJetChargeSum(Module):

    def __init__(
         self,
         inputCollection=lambda event: Collection(event, "Jet"),
         outputCollection="selectedJets",
         outputName="betaChargeSum",
         beta = 0.8,
         globalOptions={"isData": False, "year": 2016},
     ):
        self.inputCollection = inputCollection
        self.outputCollection = outputCollection
        self.outputName = outputName
        self.beta = beta
        self.globalOptions = globalOptions


    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch(self.outputCollection+"_"+self.outputName, "F", lenVar="n"+self.outputCollection)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        jets = self.inputCollection(event)  
        globalJetVars = Collection(event, "global")
        lengthJetVars = Collection(event, "length")
        cpfJetVars = Collection(event, "cpf")
        
        globalJetIndices = [globalJetVar.jetIdx for globalJetVar in globalJetVars]
        
        chargeArray = np.zeros(len(jets))
        
        for ijet, jet in enumerate(jets):
            try:
                idx = globalJetIndices.index(jet._index)
            except ValueError:
                print "WARNING: jet (pt: %s, eta: %s) does not have a matching global jet => jet charge cannot be evaluated!" % (jet.pt, jet.eta)
                continue
                

            globalJetVar = globalJetVars[idx]
            lengthJetVar = lengthJetVars[idx]
            if abs(jet.eta - globalJetVar.eta) > 0.01 or \
               abs(deltaPhi(jet.phi,globalJetVar.phi)) > 0.01:
                   print "Warning: jet might be mismatched!"
                   continue
                   
            cpfOffset = lengthJetVar.cpf_offset
            cpfLength = lengthJetVar.cpf
            
            chargeWeightedSum = 0.
            weightSum = 0.
            for icpf in range(cpfOffset,cpfOffset+cpfLength):
                weight = (cpfJetVars[icpf].ptrel*jet.pt)**self.beta
                chargeWeightedSum += weight*cpfJetVars[icpf].charge
                weightSum += weight
                
            if weightSum>0.:
                chargeArray[ijet] = chargeWeightedSum/weightSum
            
        self.out.fillBranch(self.outputCollection+"_"+self.outputName, chargeArray)
        

        return True

