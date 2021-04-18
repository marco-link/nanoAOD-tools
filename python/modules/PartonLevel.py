from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from gen_helper import *

import math
from utils import deltaR

class PartonLevel(Module):
    def __init__(self):
        pass

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch('partonLevel_lepton_pt', "F")
        self.out.branch('partonLevel_lepton_eta', "F")
        self.out.branch('partonLevel_lepton_pdgId', "I")

        self.out.branch('partonLevel_w_pt', "F")
        self.out.branch('partonLevel_w_eta', "F")
        self.out.branch('partonLevel_w_charge', "I")
        
        #self.out.branch('partonLevel_q_pt', "F")
        #self.out.branch('partonLevel_q_eta', "F")
        
        self.out.branch('partonLevel_b_pt', "F")
        self.out.branch('partonLevel_b_eta', "F")
        self.out.branch('partonLevel_b_charge', "I")
        
        self.out.branch('partonLevel_top_pt', "F")
        self.out.branch('partonLevel_top_rapidity', "F")

        self.out.branch('partonLevel_chargeCorrelation', "F")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
    
        genParticles = Collection(event,"GenPart")
        wboson = None
        lepton = None
        top = None
        bquarks = []
        lquarks = []
        for genParticle in genParticles:
            if not (fromHardProcess(genParticle)):
                continue
                
            if abs(genParticle.pdgId)==24 and isLastCopy(genParticle):
                if wboson!=None:
                    print "WARNING - multiple W boson at gen level"
                wboson = genParticle
            
            if (abs(genParticle.pdgId) in [11,13,15]) and isLastCopy(genParticle) and isPrompt(genParticle):
                if lepton!=None:
                    print "WARNING - multiple leptons at gen level"
                lepton = genParticle
                
            if abs(genParticle.pdgId)==6 and isLastCopy(genParticle):
                if top!=None:
                    print "WARNING - multiple tops at gen level"
                top = genParticle
            
            if (abs(genParticle.pdgId) in [1,2,3,4]) and isLastCopy(genParticle):
                lquarks.append(genParticle)
                
            if abs(genParticle.pdgId)==5 and isLastCopy(genParticle):
                bquarks.append(genParticle)

        bquarks = sorted(bquarks,key=lambda x: x.pt, reverse=True)
        #print top,lepton.pdgId,len(bquarks)#bquarks[0].pdgId,bquarks[1].pdgId

        #filter out bquarks from gluons
        for bquark in bquarks[:]:
            motherIdx = bquark.genPartIdxMother
            while (motherIdx>=0 and abs(genParticles[motherIdx].pdgId)==5):
                motherIdx = genParticles[motherIdx].genPartIdxMother
                
            if (genParticles[motherIdx].pdgId==21):
                bquarks.remove(bquark)
            
        
        if lepton==None:
            self.out.fillBranch('partonLevel_lepton_pt', -1)
            self.out.fillBranch('partonLevel_lepton_eta', 0)
            self.out.fillBranch('partonLevel_lepton_pdgId', 0)
        else:
            self.out.fillBranch('partonLevel_lepton_pt', lepton.pt)
            self.out.fillBranch('partonLevel_lepton_eta', lepton.eta)
            self.out.fillBranch('partonLevel_lepton_pdgId', lepton.pdgId)
            
        if wboson==None:
            self.out.fillBranch('partonLevel_w_pt',-1)
            self.out.fillBranch('partonLevel_w_eta', 0)
            self.out.fillBranch('partonLevel_w_charge', 0)
        else:
            self.out.fillBranch('partonLevel_w_pt', wboson.pt)
            self.out.fillBranch('partonLevel_w_eta', wboson.eta)
            self.out.fillBranch('partonLevel_w_charge', getChargeFromPDG(wboson))
        
        if len(bquarks)==0:
            self.out.fillBranch('partonLevel_b_pt', -1)
            self.out.fillBranch('partonLevel_b_eta', 0)
            self.out.fillBranch('partonLevel_b_charge', 0)
           
        else:
            self.out.fillBranch('partonLevel_b_pt', bquarks[0].pt)
            self.out.fillBranch('partonLevel_b_eta', bquarks[0].eta)
            self.out.fillBranch('partonLevel_b_charge', -1 if bquarks[0].pdgId>0 else 1)

        if top==None:
            self.out.fillBranch('partonLevel_top_pt', -1)
            self.out.fillBranch('partonLevel_top_rapidity', 0)
        else:
            self.out.fillBranch('partonLevel_top_pt', top.pt)
            self.out.fillBranch('partonLevel_top_rapidity', top.p4().Rapidity())
        
        if lepton!=None and len(bquarks)>0:
            self.out.fillBranch('partonLevel_chargeCorrelation', (-1 if bquarks[0].pdgId>0 else 1)*getChargeFromPDG(lepton))
        else:
            self.out.fillBranch('partonLevel_chargeCorrelation',0)
            
        return True

