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

class TTbarReconstructionTemplate(Module):

    MTOP = 172.5

    def __init__(
         self,
         bJetCollection=lambda event: [],
         lJetCollection=lambda event: [],
         leptonObject=lambda event: Collection(event, "Muon")[0],
         wbosonCollection=lambda event: [],
         metObject=lambda event: Object("MET"),
         outputFileName="ttbarTemplates.root",
     ):
        self.bJetCollection = bJetCollection
        self.lJetCollection = lJetCollection
        self.leptonObject = leptonObject
        self.wbosonCollection = wbosonCollection
        self.metObject = metObject
        
        self.outputFileName = outputFileName
        
    def beginJob(self):
        self.leptonicTemplate = ROOT.TH1F("leptonic",";mtop;",100,100,300)
        self.leptonicTemplate.SetDirectory(0)
        
        self.hadronicTemplate = ROOT.TH2F("hadronic",";mw;mtop",100,0,200,100,100,300)
        self.hadronicTemplate.SetDirectory(0)

    def endJob(self):
        print "saving ttbar template under: ",self.outputFileName
        
        #clip templates
        for ibin in range(self.leptonicTemplate.GetNbinsX()):
            if self.leptonicTemplate.GetBinContent(ibin+1)<4:
                self.leptonicTemplate.SetBinContent(ibin+1,0)
        
        for ibin in range(self.hadronicTemplate.GetNbinsX()):
            for jbin in range(self.hadronicTemplate.GetNbinsY()):
                if self.hadronicTemplate.GetBinContent(ibin+1,jbin+1)<4:
                    self.hadronicTemplate.SetBinContent(ibin+1,jbin+1,0)
        
        #remove under/overflow
        self.leptonicTemplate.SetBinContent(0,0)
        self.leptonicTemplate.SetBinContent(self.leptonicTemplate.GetNbinsX()+1,0)
        
        for ibin in range(self.hadronicTemplate.GetNbinsX()+2):
            self.hadronicTemplate.SetBinContent(ibin,0,0)
            self.hadronicTemplate.SetBinContent(ibin,self.hadronicTemplate.GetNbinsY()+1,0)
        
        for jbin in range(self.hadronicTemplate.GetNbinsY()+2):
            self.hadronicTemplate.SetBinContent(0,jbin,0,0)
            self.hadronicTemplate.SetBinContent(self.hadronicTemplate.GetNbinsX()+1,jbin,0)
        
        
        #smooth templates        
        leptonicTemplateSmooth = self.leptonicTemplate.Clone()
        leptonicTemplateSmooth.Scale(0.)
        for _ in range(10):
            for ibin in range(1,self.leptonicTemplate.GetNbinsX()-1):
                leptonicTemplateSmooth.SetBinContent(
                    ibin+1,
                    0.5*self.leptonicTemplate.GetBinContent(ibin+1) \
                    +0.25*self.leptonicTemplate.GetBinContent(ibin) \
                    +0.25*self.leptonicTemplate.GetBinContent(ibin+2) 
                )
            for ibin in range(self.leptonicTemplate.GetNbinsX()):
                self.leptonicTemplate.SetBinContent(ibin+1,leptonicTemplateSmooth.GetBinContent(ibin+1))
                
                
        hadronicTemplateSmooth = self.hadronicTemplate.Clone()
        hadronicTemplateSmooth.Scale(0.)
        for _ in range(10):
            for ibin in range(1,self.hadronicTemplate.GetNbinsX()-1):
                for jbin in range(1,self.hadronicTemplate.GetNbinsY()-1):
                    hadronicTemplateSmooth.SetBinContent(
                        ibin+1,jbin+1,
                        0.5*self.hadronicTemplate.GetBinContent(ibin+1,jbin+1) \
                        
                        +0.075*self.hadronicTemplate.GetBinContent(ibin,jbin+1) \
                        +0.075*self.hadronicTemplate.GetBinContent(ibin+2,jbin+1) \
                        +0.075*self.hadronicTemplate.GetBinContent(ibin+1,jbin) \
                        +0.075*self.hadronicTemplate.GetBinContent(ibin+1,jbin+2) \
                        
                        +0.05*self.hadronicTemplate.GetBinContent(ibin+2,jbin+2) \
                        +0.05*self.hadronicTemplate.GetBinContent(ibin+2,jbin) \
                        +0.05*self.hadronicTemplate.GetBinContent(ibin,jbin+2) \
                        +0.05*self.hadronicTemplate.GetBinContent(ibin,jbin) 
                    )
            for ibin in range(self.hadronicTemplate.GetNbinsX()):
                for jbin in range(self.hadronicTemplate.GetNbinsY()):
                    self.hadronicTemplate.SetBinContent(ibin+1, jbin+1, hadronicTemplateSmooth.GetBinContent(ibin+1, jbin+1))
                    
        outputFile = ROOT.TFile(self.outputFileName,"RECREATE")
        self.leptonicTemplate.SetDirectory(outputFile)
        self.hadronicTemplate.SetDirectory(outputFile)
        outputFile.Write()
        outputFile.Close()
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
        
    def matchJetToQuark(self,jets,quark,dRmatch=0.4):
        bestJet = None
        minDR = 1e3
        for jet in jets:
            dR = deltaR(jet,quark)
            if dR<dRmatch and minDR>dR:
                bestJet = jet
                minDR = dR
        return bestJet
       
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        bjets = self.bJetCollection(event)
        ljets = self.lJetCollection(event)
        lepton = self.leptonObject(event)
        wbosons = self.wbosonCollection(event)
        met = self.metObject(event)
        
        if len(ljets)<2 or len(bjets)<2 or len(wbosons)==0:
            return True
        
        topQuarks = {}

        genParticles = Collection(event,"GenPart")

        for idx,genParticle in enumerate(genParticles):
            absId = abs(genParticle.pdgId)
            if absId in [1,2,3,4,11,12,13,14,15,16]:
                motherIdx = genParticle.genPartIdxMother
                if motherIdx>=0 and abs(genParticles[motherIdx].pdgId)==24:
                    wbosonIdx = motherIdx
                
                    while motherIdx>=0 and abs(genParticles[motherIdx].pdgId)!=6:
                        motherIdx = genParticles[motherIdx].genPartIdxMother
                    if motherIdx>=0:
                        topIdx = motherIdx
                        if topIdx not in topQuarks.keys():
                            topQuarks[topIdx] = {"w": None, "b": None, "wdecay": [], "isHadronic": False}
                        topQuarks[topIdx]["w"] = wbosonIdx
                        topQuarks[topIdx]["wdecay"].append(idx)
                        topQuarks[topIdx]["isHadronic"] = absId in [1,2,3,4]
                       
            elif absId==5:
                motherIdx = genParticle.genPartIdxMother
                if motherIdx>=0 and abs(genParticles[motherIdx].pdgId)==6:
                    topIdx = motherIdx
                    if topIdx not in topQuarks.keys():
                        topQuarks[topIdx] = {"w": None, "b": None, "wdecay": [], "isHadronic": False}
                    topQuarks[topIdx]["b"] = idx
            
                        
        for idx,topQuark in topQuarks.items():
            if topQuark["w"]==None or topQuark["b"]==None or len(topQuark["wdecay"])!=2:
                print "WARNING: weird genlevel info in TTbarReconstructionTemplate -> skip event",topQuark
                continue
                
            bjet = self.matchJetToQuark(bjets,genParticles[topQuark["b"]])
            if not bjet:
                #other
                continue
            
            if topQuark["isHadronic"]:
                wjet1 = self.matchJetToQuark(ljets,genParticles[topQuark["wdecay"][0]])
                wjet2 = self.matchJetToQuark(ljets,genParticles[topQuark["wdecay"][1]])
                
                if wjet1==None or wjet2==None:
                    #other
                    continue

                wbosonP4 = wjet1.p4()+wjet2.p4()
                topP4 = wbosonP4+bjet.p4()
                    
                self.hadronicTemplate.Fill(wbosonP4.M(),topP4.M())
                
            else:
                bestTopMass = 1e12
                for wboson in wbosons:
                    topP4 = wboson.p4()+bjet.p4()
                    if math.fabs(topP4.M()-TTbarReconstructionTemplate.MTOP)<math.fabs(bestTopMass-TTbarReconstructionTemplate.MTOP):
                        bestTopMass = topP4.M()
                self.leptonicTemplate.Fill(bestTopMass)

        
        return True

