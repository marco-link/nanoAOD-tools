import os
import sys
import math
import json
import ROOT
import random
import itertools
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaR, deltaPhi, PhysicsObject

class TTbarReconstruction(Module):

    MTOP = 172.5
    PROBMIN = math.exp(-30)

    def __init__(
         self,
         bJetCollection=lambda event: [],
         lJetCollection=lambda event: [],
         leptonObject=lambda event: Collection(event, "Muon")[0],
         wbosonCollection=lambda event: [],
         metObject=lambda event: Object("MET"),
         templateFile="",
         taggerName = None,
         isMC = True,
         outputName="ttbar",
         systName="nominal",
     ):
        self.bJetCollection = bJetCollection
        self.lJetCollection = lJetCollection
        self.leptonObject = leptonObject
        self.wbosonCollection = wbosonCollection
        self.metObject = metObject
        
        self.templateFile = os.path.expandvars(templateFile)
        self.outputName = outputName
        self.systName = systName
        self.taggerName = taggerName
        self.isMC = isMC

        rootFile = ROOT.TFile(self.templateFile)
        if not rootFile:
            raise Exception("Error loading template file '%s'"%self.templateFile)
        self.leptonicTemplate = rootFile.Get("leptonic")
        if not self.leptonicTemplate:
            raise Exception("Error loading leptonic template from file '%s'"%self.templateFile)
        self.hadronicTemplate = rootFile.Get("hadronic")
        if not self.hadronicTemplate:
            raise Exception("Error loading hadronic template from file '%s'"%self.templateFile)
        
        #TODO: need to scale by binwidth?
        self.leptonicTemplate.Scale(1./self.leptonicTemplate.Integral())
        self.hadronicTemplate.Scale(1./self.hadronicTemplate.Integral())
        
        self.leptonicTemplate.SetDirectory(0)
        self.hadronicTemplate.SetDirectory(0)
        rootFile.Close()

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        
        self.out.branch(self.outputName+"_wHadronic_pt_"+self.systName,"F")
        self.out.branch(self.outputName+"_wHadronic_eta_"+self.systName,"F")
        self.out.branch(self.outputName+"_wHadronic_mass_"+self.systName,"F")

        self.out.branch(self.outputName+"_topHadronic_mass_"+self.systName,"F")
        self.out.branch(self.outputName+"_topHadronic_pt_"+self.systName,"F")
        self.out.branch(self.outputName+"_topHadronic_eta_"+self.systName,"F")
        
        self.out.branch(self.outputName+"_topLeptonic_mass_"+self.systName,"F")
        self.out.branch(self.outputName+"_topLeptonic_pt_"+self.systName,"F")
        self.out.branch(self.outputName+"_topLeptonic_eta_"+self.systName,"F")
        
        self.out.branch(self.outputName+"_bjetHadronic_pt_"+self.systName,"F")
        self.out.branch(self.outputName+"_bjetHadronic_eta_"+self.systName,"F")
        
        self.out.branch(self.outputName+"_bjetLeptonic_pt_"+self.systName,"F")
        self.out.branch(self.outputName+"_bjetLeptonic_eta_"+self.systName,"F")
        
        self.out.branch(self.outputName+"_mass_"+self.systName,"F")
        self.out.branch(self.outputName+"_logProb_"+self.systName,"F")
        
        if not self.taggerName is None:
            self.out.branch(self.outputName+"_bjetLeptonic_"+self.taggerName+"_highestScoreIndex_"+self.systName,"I")
            self.out.branch(self.outputName+"_bjetHadronic_"+self.taggerName+"_highestScoreIndex_"+self.systName,"I")
            for label in Module.taggerLabels[self.taggerName]:
                self.out.branch(self.outputName+"_bjetLeptonic_"+self.taggerName+"_"+label+"_"+self.systName,"F")
                self.out.branch(self.outputName+"_bjetHadronic_"+self.taggerName+"_"+label+"_"+self.systName,"F")

        if self.isMC:
            self.out.branch(self.outputName+"_bjetLeptonic_hadronFlavour_"+self.systName,"I")
            self.out.branch(self.outputName+"_bjetLeptonic_partonFlavour_"+self.systName,"I")
            self.out.branch(self.outputName+"_bjetHadronic_hadronFlavour_"+self.systName,"I")
            self.out.branch(self.outputName+"_bjetHadronic_partonFlavour_"+self.systName,"I")
            self.out.branch(self.outputName+"_ljetFromW_1_hadronFlavour_"+self.systName,"I")
            self.out.branch(self.outputName+"_ljetFromW_1_partonFlavour_"+self.systName,"I")
            self.out.branch(self.outputName+"_ljetFromW_2_hadronFlavour_"+self.systName,"I")
            self.out.branch(self.outputName+"_ljetFromW_2_partonFlavour_"+self.systName,"I")
        
        
    def getLeptonicLogProbability(self,mLeptonicTop):
        ibin = self.leptonicTemplate.GetXaxis().FindBin(mLeptonicTop)
        if ibin<=1 or ibin>=(self.leptonicTemplate.GetXaxis().GetNbins()-1):
            return math.log(TTbarReconstruction.PROBMIN)
        
        return math.log(max(
            TTbarReconstruction.PROBMIN,
            self.leptonicTemplate.GetBinContent(ibin)
        ))
            
    def getHadronicLogProbability(self,mHadronicW,mHadronicTop):
        #todo: can fill into array or do some interpolation for faster lookup
    
        ibin = self.hadronicTemplate.GetXaxis().FindBin(mHadronicW)
        if ibin<=1 or ibin>=(self.hadronicTemplate.GetXaxis().GetNbins()-1):
            return math.log(TTbarReconstruction.PROBMIN)
        jbin = self.hadronicTemplate.GetYaxis().FindBin(mHadronicTop)
        if jbin<=1 or jbin>=(self.hadronicTemplate.GetYaxis().GetNbins()-1):
            return math.log(TTbarReconstruction.PROBMIN)
            
        return math.log(max(
            TTbarReconstruction.PROBMIN,
            self.hadronicTemplate.GetBinContent(ibin,jbin)
        ))
            
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        bjets = self.bJetCollection(event)
        ljets = self.lJetCollection(event)
        lepton = self.leptonObject(event)
        wbosons = self.wbosonCollection(event)
        met = self.metObject(event)
        
        if len(ljets)<2 or len(bjets)<2 or len(wbosons)==0:
            self.out.fillBranch(self.outputName+"_wHadronic_pt_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_wHadronic_eta_"+self.systName,0)
            self.out.fillBranch(self.outputName+"_wHadronic_mass_"+self.systName,-1)

            self.out.fillBranch(self.outputName+"_topHadronic_mass_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_topHadronic_pt_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_topHadronic_eta_"+self.systName,0)
            
            self.out.fillBranch(self.outputName+"_topLeptonic_mass_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_topLeptonic_pt_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_topLeptonic_eta_"+self.systName,0)
            
            self.out.fillBranch(self.outputName+"_bjetHadronic_pt_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_bjetHadronic_eta_"+self.systName,0)
            
            self.out.fillBranch(self.outputName+"_bjetLeptonic_pt_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_bjetLeptonic_eta_"+self.systName,0)
            
            self.out.fillBranch(self.outputName+"_mass_"+self.systName,-1)
            self.out.fillBranch(self.outputName+"_logProb_"+self.systName,math.log(TTbarReconstruction.PROBMIN))
            return True

        permutations = []
        
        for bjetCombination in itertools.combinations(bjets,2):
            for ljetCombination in itertools.combinations(ljets,2):
                for ibjet in range(len(bjetCombination)):
                    bFromHadronicTop = bjetCombination[ibjet]
                    bFromLeptonicTop = bjetCombination[(ibjet+1)%2]
                    
                    wbosonFromHadronicTopP4 = ljetCombination[0].p4()+ljetCombination[1].p4()
                    hadronicTopP4 = wbosonFromHadronicTopP4+bFromHadronicTop.p4()
                    
                    bestLeptonicTopMass = 1e12
                    bestLeptonicTopP4 = None
                    for leptonicWboson in wbosons:
                        leptonicTopP4 = leptonicWboson.p4()+bFromLeptonicTop.p4()
                        if math.fabs(leptonicTopP4.M()-TTbarReconstruction.MTOP)<math.fabs(bestLeptonicTopMass-TTbarReconstruction.MTOP):
                            bestTopMass = leptonicTopP4.M()
                            bestLeptonicTopP4 = leptonicTopP4
                            
                    logProbL = self.getLeptonicLogProbability(bestLeptonicTopP4.M())
                    logProbH = self.getHadronicLogProbability(wbosonFromHadronicTopP4.M(),hadronicTopP4.M())
                    
                    permutations.append({
                        "logProb": max(math.log(TTbarReconstruction.PROBMIN),logProbH+logProbL),
                        "logProbH": logProbH,
                        "logProbL": logProbL,
                        "hadronicTopP4": hadronicTopP4,
                        "leptonicTopP4": hadronicTopP4,
                        "jetsFromW":ljetCombination,
                        "wbosonFromHadronicTopP4": wbosonFromHadronicTopP4,
                        "bFromLeptonicTop": bFromLeptonicTop,
                        "bFromHadronicTop": bFromHadronicTop,
                        "ljetFromW_1": ljetCombination[0],
                        "ljetFromW_2": ljetCombination[1],
                    })
        permutations = sorted(permutations,key=lambda x: x['logProb'], reverse=True)
        bestPermutation = permutations[0]
        
        
        self.out.fillBranch(self.outputName+"_wHadronic_pt_"+self.systName,bestPermutation["wbosonFromHadronicTopP4"].Pt())
        self.out.fillBranch(self.outputName+"_wHadronic_eta_"+self.systName,bestPermutation["wbosonFromHadronicTopP4"].Eta())
        self.out.fillBranch(self.outputName+"_wHadronic_mass_"+self.systName,bestPermutation["wbosonFromHadronicTopP4"].M())

        self.out.fillBranch(self.outputName+"_topHadronic_mass_"+self.systName,bestPermutation["hadronicTopP4"].M())
        self.out.fillBranch(self.outputName+"_topHadronic_pt_"+self.systName,bestPermutation["hadronicTopP4"].Pt())
        self.out.fillBranch(self.outputName+"_topHadronic_eta_"+self.systName,bestPermutation["hadronicTopP4"].Eta())
        
        self.out.fillBranch(self.outputName+"_topLeptonic_mass_"+self.systName,bestPermutation["leptonicTopP4"].M())
        self.out.fillBranch(self.outputName+"_topLeptonic_pt_"+self.systName,bestPermutation["leptonicTopP4"].Pt())
        self.out.fillBranch(self.outputName+"_topLeptonic_eta_"+self.systName,bestPermutation["leptonicTopP4"].Eta())
        
        self.out.fillBranch(self.outputName+"_bjetHadronic_pt_"+self.systName,bestPermutation["bFromHadronicTop"].pt)
        self.out.fillBranch(self.outputName+"_bjetHadronic_eta_"+self.systName,bestPermutation["bFromHadronicTop"].eta)
        
        self.out.fillBranch(self.outputName+"_bjetLeptonic_pt_"+self.systName,bestPermutation["bFromLeptonicTop"].pt)
        self.out.fillBranch(self.outputName+"_bjetLeptonic_eta_"+self.systName,bestPermutation["bFromLeptonicTop"].eta)

        if not self.taggerName is None:
            self.out.fillBranch(self.outputName+"_bjetLeptonic_"+self.taggerName+"_highestScoreIndex_"+self.systName,
                                Module.taggerLabels[self.taggerName].index(max(getattr(bestPermutation["bFromLeptonicTop"],self.taggerName),
                                                                               key = lambda k: getattr(bestPermutation["bFromLeptonicTop"],self.taggerName)[k])))
            self.out.fillBranch(self.outputName+"_bjetHadronic_"+self.taggerName+"_highestScoreIndex_"+self.systName,
                                Module.taggerLabels[self.taggerName].index(max(getattr(bestPermutation["bFromHadronicTop"],self.taggerName),
                                                                               key = lambda k: getattr(bestPermutation["bFromHadronicTop"],self.taggerName)[k])))

            for label in Module.taggerLabels[self.taggerName]:
                self.out.fillBranch(self.outputName+"_bjetLeptonic_"+self.taggerName+"_"+label+"_"+self.systName,getattr(bestPermutation["bFromLeptonicTop"],self.taggerName)[label])
                self.out.fillBranch(self.outputName+"_bjetHadronic_"+self.taggerName+"_"+label+"_"+self.systName,getattr(bestPermutation["bFromHadronicTop"],self.taggerName)[label])

        if self.isMC:
            self.out.fillBranch(self.outputName+"_bjetLeptonic_hadronFlavour_"+self.systName,getattr(bestPermutation["bFromLeptonicTop"],"hadronFlavour"))
            self.out.fillBranch(self.outputName+"_bjetLeptonic_partonFlavour_"+self.systName,getattr(bestPermutation["bFromLeptonicTop"],"partonFlavour"))
            self.out.fillBranch(self.outputName+"_bjetHadronic_hadronFlavour_"+self.systName,getattr(bestPermutation["bFromHadronicTop"],"hadronFlavour"))
            self.out.fillBranch(self.outputName+"_bjetHadronic_partonFlavour_"+self.systName,getattr(bestPermutation["bFromHadronicTop"],"partonFlavour"))
            self.out.fillBranch(self.outputName+"_ljetFromW_1_hadronFlavour_"+self.systName,getattr(bestPermutation["ljetFromW_1"],"hadronFlavour"))
            self.out.fillBranch(self.outputName+"_ljetFromW_1_partonFlavour_"+self.systName,getattr(bestPermutation["ljetFromW_1"],"partonFlavour"))
            self.out.fillBranch(self.outputName+"_ljetFromW_2_hadronFlavour_"+self.systName,getattr(bestPermutation["ljetFromW_2"],"hadronFlavour"))
            self.out.fillBranch(self.outputName+"_ljetFromW_2_partonFlavour_"+self.systName,getattr(bestPermutation["ljetFromW_2"],"partonFlavour"))
        
        self.out.fillBranch(self.outputName+"_mass_"+self.systName,(bestPermutation["hadronicTopP4"]+bestPermutation["leptonicTopP4"]).M())
        self.out.fillBranch(self.outputName+"_logProb_"+self.systName,bestPermutation['logProb'])
        
        #for permutation in permutations:
        #    print permutation['logProb'],permutation['logProbH'],permutation['logProbL'],permutation['hadronicTopP4'].M()
        #print
        
        return True

