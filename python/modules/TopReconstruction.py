import os
import sys
import math
import json
import ROOT
import random
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaR, deltaPhi, PhysicsObject

class TopReconstruction(Module):

    MTOP = 172.5

    def __init__(
         self,
         bJetCollection=lambda event: [],
         lJetCollection=lambda event: [],
         leptonObject=lambda event: Collection(event, "Muon")[0],
         wbosonCollection=lambda event: [],
         metObject=lambda event: Object("MET"),
         outputName="top",
         globalOptions={"isData": False, "year": 2016},
     ):
        self.bJetCollection = bJetCollection
        self.lJetCollection = lJetCollection
        self.leptonObject = leptonObject
        self.wbosonCollection = wbosonCollection
        self.metObject = metObject
        
        self.outputName = outputName
        self.globalOptions = globalOptions
        


    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch(self.outputName+"_top_mass", "F")
        self.out.branch(self.outputName+"_top_pt", "F")
        self.out.branch(self.outputName+"_top_eta", "F")
        self.out.branch(self.outputName+"_top_cosPolarization", "F")
        
        self.out.branch(self.outputName+"_ljet_eta", "F")
        self.out.branch(self.outputName+"_bjet_lepton_deta", "F")
        self.out.branch(self.outputName+"_ljet_bjet_dR", "F")
        self.out.branch(self.outputName+"_wboson_cosHelicity", "F")
        
        self.out.branch(self.outputName+"_eventShape_isotropy", "F")
        self.out.branch(self.outputName+"_eventShape_circularity", "F")
        self.out.branch(self.outputName+"_eventShape_sphericity", "F")
        self.out.branch(self.outputName+"_eventShape_aplanarity", "F")
        self.out.branch(self.outputName+"_eventShape_C", "F")
        
        
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        bjets = self.bJetCollection(event)
        ljets = self.lJetCollection(event)
        lepton = self.leptonObject(event)
        wbosons = self.wbosonCollection(event)
        met = self.metObject(event)
        
        if len(ljets)==0 or len(bjets)==0 or len(wbosons)==0:
            self.out.fillBranch(self.outputName+"_top_mass", -1.0)
            self.out.fillBranch(self.outputName+"_top_pt", -1.0)
            self.out.fillBranch(self.outputName+"_top_eta", 0.0)
            self.out.fillBranch(self.outputName+"_top_cosPolarization", 0.0)
            
            self.out.fillBranch(self.outputName+"_ljet_eta", 0.0)
            self.out.fillBranch(self.outputName+"_bjet_lepton_deta", 0.0)
            self.out.fillBranch(self.outputName+"_ljet_bjet_dR", 0.0)
            self.out.fillBranch(self.outputName+"_wboson_cosHelicity", 0.0)
            return True
            
        ljet = sorted(ljets,key=lambda x: math.fabs(x.eta), reverse=True)[0] #take most forward
        bjet = sorted(bjets,key=lambda x: x.pt, reverse=True)[0] #take highest pT
        
        eventShapes = ROOT.EventShapes()
        eventShapes.addObject(lepton.pt, lepton.eta, lepton.phi, 0.0)
        eventShapes.addObject(ljet.pt, ljet.eta, ljet.phi, 0.0)
        eventShapes.addObject(bjet.pt, bjet.eta, bjet.phi, 0.0)
        eventShapes.addObject(met.pt, 0.0, met.phi, 0.0)
        
        self.out.fillBranch(self.outputName+"_eventShape_isotropy", eventShapes.isotropy())
        self.out.fillBranch(self.outputName+"_eventShape_circularity", eventShapes.circularity())
        self.out.fillBranch(self.outputName+"_eventShape_sphericity", eventShapes.sphericity())
        self.out.fillBranch(self.outputName+"_eventShape_aplanarity", eventShapes.aplanarity())
        self.out.fillBranch(self.outputName+"_eventShape_C", eventShapes.C())
        
        #take wboson that gives candidate mass closest to mtop
        mbestTop = 1000000
        
        for i in range(len(wbosons)):
            topP4 = wbosons[i].p4()+bjet.p4()
            if math.fabs(min(mbestTop-1,topP4.M())-TopReconstruction.MTOP)<mbestTop:
                mbestTop = topP4.M()
                wboson = wbosons[i]
                top = PhysicsObject(None, pt=topP4.Pt(), eta=topP4.Eta(), phi=topP4.Phi(), mass=topP4.M())
   
        

        setattr(event,self.outputName+"_top_candidate",top)
        
        #TODO: this is buggy
        leptonInWbosonRestframe = lepton.p4()
        leptonInWbosonRestframe.Boost(-wboson.p4().BoostVector())
        topInWbosonRestframe = -top.p4()
        topInWbosonRestframe.Boost(-wboson.p4().BoostVector())
        cosWPol = leptonInWbosonRestframe.Vect().Dot(topInWbosonRestframe.Vect())/leptonInWbosonRestframe.Vect().Mag()/topInWbosonRestframe.Vect().Mag()
        
        leptonInTopRestframe = lepton.p4()
        leptonInTopRestframe.Boost(-top.p4().BoostVector())
        ljetInTopRestframe = ljet.p4()
        ljetInTopRestframe.Boost(-top.p4().BoostVector())
        cosTopPol = leptonInTopRestframe.Vect().Dot(ljetInTopRestframe.Vect())/leptonInTopRestframe.Vect().Mag()/ljetInTopRestframe.Vect().Mag()
        
        
        self.out.fillBranch(self.outputName+"_top_mass", top.mass)
        self.out.fillBranch(self.outputName+"_top_pt", top.pt)
        self.out.fillBranch(self.outputName+"_top_eta", top.eta)
        self.out.fillBranch(self.outputName+"_top_cosPolarization", cosTopPol)
        
        self.out.fillBranch(self.outputName+"_ljet_eta", ljet.eta)
        self.out.fillBranch(self.outputName+"_bjet_lepton_deta", math.fabs(bjet.eta-lepton.eta))
        self.out.fillBranch(self.outputName+"_ljet_bjet_dR", deltaR(ljet,bjet))
        self.out.fillBranch(self.outputName+"_wboson_cosHelicity", cosWPol)
        
        return True

