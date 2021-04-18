from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from gen_helper import *

import math
from utils import deltaR

class ParticleLevel(Module):
    def __init__(self):
        pass

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch('particleLevel_lepton_pt', "F")
        self.out.branch('particleLevel_lepton_eta', "F")
        self.out.branch('particleLevel_lepton_pdgId', "I")

        self.out.branch('particleLevel_met_pt', "F")
        self.out.branch('particleLevel_met_phi', "F")
        
        self.out.branch('particleLevel_njet', "F")
        self.out.branch('particleLevel_nbjet', "F")
        
        self.out.branch('particleLevel_ljet_pt', "F")
        self.out.branch('particleLevel_ljet_eta', "F")
        
        self.out.branch('particleLevel_bjet_pt', "F")
        self.out.branch('particleLevel_bjet_eta', "F")
        self.out.branch('particleLevel_bjet_charge', "I")
        
        #TODO
        #self.out.branch('particleLevel_top_pt', "F")
        #self.out.branch('particleLevel_top_rapidity', "F")
        #self.out.branch('particleLevel_top_mass', "F")

        self.out.branch('particleLevel_chargeCorrelation', "F")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
    
        dressedLeptons = Collection(event,"GenDressedLepton")
        genJets = Collection(event,"GenJet")
        met = Object(event,"MET")
        genMet = ROOT.TLorentzVector()
        genMet.SetPtEtaPhiM(met.fiducialGenPt, 0., met.fiducialGenPhi, 0.)
        
        self.out.fillBranch('particleLevel_met_pt', met.fiducialGenPt)
        self.out.fillBranch('particleLevel_met_phi', met.fiducialGenPhi)
        
        leptons = []
        for lepton in dressedLeptons:
            if lepton.pt<25 or math.fabs(lepton.eta)>2.4:
                continue
            leptons.append(lepton)
        
        leptons = sorted(leptons,key=lambda x: x.pt, reverse=True)    
        
        if len(leptons)!=1 or leptons[0].pt<26 or math.fabs(leptons[0].eta)>2.4:
            lepton = None
            self.out.fillBranch('particleLevel_lepton_pt', -1)
            self.out.fillBranch('particleLevel_lepton_eta', 0)
            self.out.fillBranch('particleLevel_lepton_pdgId', 0)
        else:
            lepton = leptons[0]
            self.out.fillBranch('particleLevel_lepton_pt', lepton.pt)
            self.out.fillBranch('particleLevel_lepton_eta', lepton.eta)
            self.out.fillBranch('particleLevel_lepton_pdgId', lepton.pdgId)
        
        ljets = []
        bjets = []
        for jet in genJets:
            if lepton and deltaR(jet,lepton)<0.4:
                continue
            if abs(jet.hadronFlavour)==5 and jet.pt>30 and math.fabs(jet.eta)<2.4:
                bjets.append(jet)
            elif jet.pt>30 and math.fabs(jet.eta)<4.7:
                ljets.append(jet)
        
        self.out.fillBranch('particleLevel_njet', len(ljets)+len(bjets))
        self.out.fillBranch('particleLevel_nbjet', len(bjets))
        
        if len(ljets)==0:
            ljet = None
            self.out.fillBranch('particleLevel_ljet_pt', -1)
            self.out.fillBranch('particleLevel_ljet_eta', 0)
        else:
            ljet = sorted(ljets,key=lambda x: math.fabs(x.eta), reverse=True)[0] #most forward
            self.out.fillBranch('particleLevel_ljet_pt', ljet.pt)
            self.out.fillBranch('particleLevel_ljet_eta', ljet.eta)
            
        if len(bjets)==0:
            bjet = None
            self.out.fillBranch('particleLevel_bjet_pt', -1)
            self.out.fillBranch('particleLevel_bjet_eta', 0)
            self.out.fillBranch('particleLevel_bjet_charge', 0)
        else:
            bjet = sorted(bjets,key=lambda x: x.pt, reverse=True)[0] #highest pT
            self.out.fillBranch('particleLevel_bjet_pt', bjet.pt)
            self.out.fillBranch('particleLevel_bjet_eta', bjet.eta)
            
            #note: hadronflavour does not store the sign
            if bjet.partonFlavour==5:
                bcharge = -1 #b
            elif bjet.partonFlavour==-5:
                bcharge = 1 #bbar
            else:
                bcharge = 0
            self.out.fillBranch('particleLevel_bjet_charge', bcharge)
            
        if bjet!=None and lepton!=None:
            self.out.fillBranch('particleLevel_chargeCorrelation', bcharge*getChargeFromPDG(lepton))
        else:
            self.out.fillBranch('particleLevel_chargeCorrelation', 0)
        
        #TODO
        #self.out.branch('particleLevel_top_pt', "F")
        #self.out.branch('particleLevel_top_rapidity', "F")
        #self.out.branch('particleLevel_top_mass', "F")

        return True

