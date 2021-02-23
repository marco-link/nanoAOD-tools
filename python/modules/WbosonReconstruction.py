import os
import sys
import math
import json
import ROOT
import random
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaPhi, PhysicsObject

class WbosonReconstruction(Module):
    MW = 80.4

    def __init__(self,
        leptonObject = lambda event: Collection(event,"Muon")[0],
        metObject =lambda event: Object(event, "MET"),
        globalOptions={"isData":False}, 
        outputName='nominal'
    ):
        self.leptonObject = leptonObject
        self.metObject = metObject
        self.globalOptions=globalOptions
        self.outputName=outputName
       
        
    def beginJob(self):
        pass
        
    def endJob(self):
        pass
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch(self.outputName+"_met", "F")
        self.out.branch(self.outputName+"_mtw", "F")
        self.out.branch(self.outputName+"_met_lepton_deltaPhi", "F")
        
        self.out.branch(self.outputName+"_wreco_constant", "F")
        self.out.branch(self.outputName+"_wreco_radicand", "F")
            
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
        
    def makeWbosonCandidate(self,metPx,metPy,pz,leptonP4):
        nuP4 = ROOT.TLorentzVector(metPx,metPy,pz,math.sqrt(metPx**2+metPy**2+pz**2))  
        wP4 = nuP4+leptonP4
        return PhysicsObject(None, pt=wP4.Pt(), eta=wP4.Eta(), phi=wP4.Phi(), mass= wP4.M())
    
        
    def analyze(self, event):
        lepton = self.leptonObject(event)
        met = self.metObject(event)
        
        
        dPhi = deltaPhi(lepton,met)
        mtw = math.sqrt(2*lepton.pt*met.pt*(1-math.cos(dPhi)))
        
        self.out.fillBranch(self.outputName+"_met", met.pt)
        self.out.fillBranch(self.outputName+"_mtw", mtw)
        self.out.fillBranch(self.outputName+"_met_lepton_deltaPhi", dPhi)
   
        leptonP4 = lepton.p4()
        leptonE = leptonP4.E()
        leptonPx = leptonP4.Px()
        leptonPy = leptonP4.Py()
        leptonPz = leptonP4.Pz()

        metPx = met.pt*math.cos(met.phi)
        metPy = met.pt*math.sin(met.phi)
        
        mu = WbosonReconstruction.MW**2/2. + metPx*leptonPx + metPy*leptonPy
        a  = (mu * leptonPz) / (leptonE**2 - leptonPz**2)
        b  = (leptonE**2 * met.pt**2 - mu**2) / (leptonE**2 - leptonPz**2)
        
        radicand = a**2-b
        
        self.out.fillBranch(self.outputName+"_wreco_constant", a)
        self.out.fillBranch(self.outputName+"_wreco_radicand", radicand)

        if radicand>0:
            pz1 = a + math.sqrt(radicand)
            pz2 = a - math.sqrt(radicand)
            
            #make |pz1| the smallest solution
            if math.fabs(pz1)>math.fabs(pz2):
                pz1,pz2 = pz2,pz1
                
            setattr(event,self.outputName+"_w_candidates",[
                self.makeWbosonCandidate(metPx,metPy,pz1,lepton.p4()),
                self.makeWbosonCandidate(metPx,metPy,pz2,lepton.p4())
            ])
            
        else:
            #ignore radicand
            pz = a
            setattr(event,self.outputName+"_w_candidates",[
                self.makeWbosonCandidate(metPx,metPy,pz,lepton.p4()),
            ])
        
        return True
            
            
