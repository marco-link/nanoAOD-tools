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

class SingleTopReconstruction(Module):

    MTOP = 172.5

    def __init__(
         self,
         bJetCollection=lambda event: [],
         lJetCollection=lambda event: [],
         leptonObject=lambda event: Collection(event, "Muon")[0],
         wbosonCollection=lambda event: [],
         metObject=lambda event: Object("MET"),
         taggerName = None,
         isMC = True,
         outputName="top",
         systName = "nominal",
     ):
        self.bJetCollection = bJetCollection
        self.lJetCollection = lJetCollection
        self.leptonObject = leptonObject
        self.wbosonCollection = wbosonCollection
        self.metObject = metObject
        
        self.outputName = outputName
        self.systName = systName
        self.taggerName = taggerName
        self.isMC = isMC

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        
        self.out.branch(self.outputName+"_mass_"+self.systName, "F")
        self.out.branch(self.outputName+"_pt_"+self.systName, "F")
        self.out.branch(self.outputName+"_eta_"+self.systName, "F")
        self.out.branch(self.outputName+"_cosPolz_"+self.systName, "F")
        self.out.branch(self.outputName+"_cosWhel_"+self.systName, "F")
        
        self.out.branch(self.outputName+"_ljet_eta_"+self.systName, "F")
        self.out.branch(self.outputName+"_bjet_lepton_deta_"+self.systName, "F")
        self.out.branch(self.outputName+"_bjet_ljet_dR_"+self.systName, "F")
        
        self.out.branch(self.outputName+"_bjet_pt_"+self.systName,"F")
        self.out.branch(self.outputName+"_bjet_eta_"+self.systName,"F")
        self.out.branch(self.outputName+"_ljet_pt_"+self.systName,"F")
        self.out.branch(self.outputName+"_ljet_eta_"+self.systName,"F")

        if self.isMC:
            self.out.branch(self.outputName+"_bjet_hadronFlavour_"+self.systName,"F")
            self.out.branch(self.outputName+"_bjet_partonFlavour_"+self.systName,"F")
            self.out.branch(self.outputName+"_ljet_hadronFlavour_"+self.systName,"F")
            self.out.branch(self.outputName+"_ljet_partonFlavour_"+self.systName,"F")
        
        if not self.taggerName is None:
            for label in Module.taggerLabels[self.taggerName]:
                self.out.branch(self.outputName+"_bjet_"+self.taggerName+"_"+label+"_"+self.systName,"F")
                self.out.branch(self.outputName+"_ljet_"+self.taggerName+"_"+label+"_"+self.systName,"F")

        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        bjets = self.bJetCollection(event)
        ljets = self.lJetCollection(event)
        lepton = self.leptonObject(event)
        wbosons = self.wbosonCollection(event)
        met = self.metObject(event)
        
        if len(ljets+bjets)<2 or len(wbosons)==0:
            self.out.fillBranch(self.outputName+"_mass_"+self.systName, -1)
            self.out.fillBranch(self.outputName+"_pt_"+self.systName, -1)
            self.out.fillBranch(self.outputName+"_eta_"+self.systName, 0)
            self.out.fillBranch(self.outputName+"_cosPolz_"+self.systName, -10)
            self.out.fillBranch(self.outputName+"_cosWhel_"+self.systName, -10)
            
            self.out.fillBranch(self.outputName+"_ljet_eta_"+self.systName, 0)
            self.out.fillBranch(self.outputName+"_bjet_lepton_deta_"+self.systName, -1)
            self.out.fillBranch(self.outputName+"_bjet_ljet_dR_"+self.systName, -1)
            return True
        
            
        sortedLjets = sorted(ljets,key=lambda x: math.fabs(x.eta), reverse=True) #sort forward
        sortedBjets = sorted(bjets,key=lambda x: x.pt, reverse=True) #sort pT
        
        if len(sortedLjets)>=1 and len(sortedBjets)>=1:
            #default in signal region
            ljet = sortedLjets[0] #most forward
            bjet = sortedBjets[0] #highest pt
        elif len(sortedLjets)>=2 and len(sortedBjets)==0:
            #control 0b regions
            ljet = sortedLjets[0] #most forward
            bjet = sortedLjets[-1] #most central
        elif len(sortedLjets)==0 and len(sortedBjets)>=2:
            #control 0l regions
            ljet = sortedBjets[1] #subleading pT
            bjet = sortedBjets[0] #leading pT
        
        #TODO: move to dedicated module?
        '''
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
        '''
        
        #take wboson that gives candidate mass closest to mtop
        mbestTop = 1e12
        
        for i in range(len(wbosons)):
            topP4 = wbosons[i].p4()+bjet.p4()
            if math.fabs(topP4.M()-SingleTopReconstruction.MTOP)<math.fabs(mbestTop-SingleTopReconstruction.MTOP):
                mbestTop = topP4.M()
                wboson = wbosons[i]
                top = PhysicsObject(None, pt=topP4.Pt(), eta=topP4.Eta(), phi=topP4.Phi(), mass=topP4.M())
   
        setattr(event,self.outputName,top)
        
        leptonInWbosonRestframe = lepton.p4()
        leptonInWbosonRestframe.Boost(-wboson.p4().BoostVector())
        topInWbosonRestframe = -top.p4()
        topInWbosonRestframe.Boost(-wboson.p4().BoostVector())
        if abs(leptonInWbosonRestframe.Vect().Mag()*topInWbosonRestframe.Vect().Mag()) > 0:
            cosWhel = leptonInWbosonRestframe.Vect().Dot(topInWbosonRestframe.Vect())/leptonInWbosonRestframe.Vect().Mag()/topInWbosonRestframe.Vect().Mag()
        else: cosWhel = -5
        
        leptonInTopRestframe = lepton.p4()
        leptonInTopRestframe.Boost(-top.p4().BoostVector())
        ljetInTopRestframe = ljet.p4()
        ljetInTopRestframe.Boost(-top.p4().BoostVector())
        if abs(leptonInTopRestframe.Vect().Mag()*ljetInTopRestframe.Vect().Mag()) > 0:
            cosTopPolz = leptonInTopRestframe.Vect().Dot(ljetInTopRestframe.Vect())/leptonInTopRestframe.Vect().Mag()/ljetInTopRestframe.Vect().Mag()
        else: cosTopPolz = -5
        
        self.out.fillBranch(self.outputName+"_mass_"+self.systName, top.mass)
        self.out.fillBranch(self.outputName+"_pt_"+self.systName, top.pt)
        self.out.fillBranch(self.outputName+"_eta_"+self.systName, top.eta)
        self.out.fillBranch(self.outputName+"_cosPolz_"+self.systName, cosTopPolz)
        self.out.fillBranch(self.outputName+"_cosWhel_"+self.systName, cosWhel)
        
        self.out.fillBranch(self.outputName+"_ljet_eta_"+self.systName, ljet.eta)
        self.out.fillBranch(self.outputName+"_bjet_lepton_deta_"+self.systName,  math.fabs(bjet.eta-lepton.eta))
        self.out.fillBranch(self.outputName+"_bjet_ljet_dR_"+self.systName, deltaR(ljet,bjet))

        self.out.fillBranch(self.outputName+"_bjet_pt_"+self.systName, bjet.pt)
        self.out.fillBranch(self.outputName+"_bjet_eta_"+self.systName, bjet.eta)
        self.out.fillBranch(self.outputName+"_ljet_pt_"+self.systName, ljet.pt)
        self.out.fillBranch(self.outputName+"_ljet_eta_"+self.systName, ljet.eta)

        if self.isMC:
            self.out.fillBranch(self.outputName+"_bjet_hadronFlavour_"+self.systName, getattr(bjet,"hadronFlavour"))
            self.out.fillBranch(self.outputName+"_bjet_partonFlavour_"+self.systName, getattr(bjet,"partonFlavour"))
            self.out.fillBranch(self.outputName+"_ljet_hadronFlavour_"+self.systName, getattr(ljet,"hadronFlavour"))
            self.out.fillBranch(self.outputName+"_ljet_partonFlavour_"+self.systName, getattr(ljet,"partonFlavour"))

        if not self.taggerName is None:
            for label in Module.taggerLabels[self.taggerName]:
                self.out.fillBranch(self.outputName+"_bjet_"+self.taggerName+"_"+label+"_"+self.systName,getattr(bjet,self.taggerName)[label])
                self.out.fillBranch(self.outputName+"_ljet_"+self.taggerName+"_"+label+"_"+self.systName,getattr(ljet,self.taggerName)[label])

        
        return True

