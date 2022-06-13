import os
import sys
import math
import json
import ROOT
import random
import numpy as np

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import getHist, getSFXY, deltaR

class ElectronSelection(Module):
    WP80 = 1
    WP90 = 2
    INV = 3
    NONE = 4

    def __init__(
        self,
        inputCollection = lambda event: Collection(event, "Electron"),
        outputName = "tightElectrons",
        triggerMatch=False,
        electronID = WP80,
        electronMinPt = 29.,
        electronMaxEta = 2.4,
        storeKinematics=['pt','eta'],
        storeWeights=False,
        doVariations=True,
    ):

        self.inputCollection = inputCollection
        self.outputName = outputName
        self.electronMinPt = electronMinPt
        self.electronMaxEta = electronMaxEta
        self.storeKinematics = storeKinematics
        self.storeWeights = storeWeights
        self.triggerMatch = triggerMatch
        self.doVariations = doVariations
        
        self.triggerObjectCollection = lambda event: Collection(event, "TrigObj") if triggerMatch else lambda event: []

        if Module.globalOptions["year"] == '2016preVFP':

            self.WP90SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL16preVFP/egammaEffi.txt_Ele_wp90iso_preVFP_EGM2D.root",
                "EGamma_SF2D"
            )
            self.WP80SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL16preVFP/egammaEffi.txt_Ele_wp80iso_preVFP_EGM2D.root",
                "EGamma_SF2D"
            )
            self.electronRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL16preVFP/egammaEffi_ptAbove20.txt_EGM2D_UL2016preVFP.root",
                "EGamma_SF2D"
            )

        elif Module.globalOptions["year"] == '2016':

            self.WP90SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL16postVFP/egammaEffi.txt_Ele_wp90iso_postVFP_EGM2D.root",
                "EGamma_SF2D"
            )
            self.WP80SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL16postVFP/egammaEffi.txt_Ele_wp80iso_postVFP_EGM2D.root",
                "EGamma_SF2D"
            )
            self.electronRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL16postVFP/egammaEffi_ptAbove20.txt_EGM2D_UL2016postVFP.root",
                "EGamma_SF2D"
            )

        elif Module.globalOptions["year"] == '2017':

            self.WP90SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL17/egammaEffi.txt_EGM2D_MVA90iso_UL17.root",
                "EGamma_SF2D"
            )
            self.WP80SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL17/egammaEffi.txt_EGM2D_MVA80iso_UL17.root",
                "EGamma_SF2D"
            )
            self.electronRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL17/egammaEffi_ptAbove20.txt_EGM2D_UL2017.root",
                "EGamma_SF2D"
            )

        elif Module.globalOptions["year"] == '2018':

            self.WP90SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL18/egammaEffi.txt_Ele_wp90iso_EGM2D.root",
                "EGamma_SF2D"
            )
            self.WP80SFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL18/egammaEffi.txt_Ele_wp80iso_EGM2D.root",
                "EGamma_SF2D"
            )
            self.electronRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/electrons/UL18/egammaEffi_ptAbove20.txt_EGM2D_UL2018.root",
                "EGamma_SF2D"
            )
        else:
            raise Exception("Error - invalid year for muon efficiencies")

        if electronID == ElectronSelection.WP90:
            self.electronID = lambda electron: electron.mvaFall17V2Iso_WP90==1
            self.electronIdSF = self.WP90SFHist
        elif electronID == ElectronSelection.WP80:
            self.electronID = lambda electron: electron.mvaFall17V2Iso_WP80==1
            self.electronIdSF = self.WP80SFHist
        elif electronID == ElectronSelection.INV: 
            self.electronID = lambda electron: electron.mvaFall17V2Iso_WP80==0
            self.storeWeights = False
        elif electronID == ElectronSelection.NONE:
            self.storeWeights = False
            self.electronID = lambda electron: True
        else:
            raise Exception("Electron ID undefined")



    def triggerMatched(self, electron, trigger_object):
        if self.triggerMatch:
            trig_deltaR = math.pi
            for trig_obj in trigger_object:
                if abs(trig_obj.id) != 11:
                    continue
                trig_deltaR = min(trig_deltaR, deltaR(trig_obj, muon))
            if trig_deltaR < 0.3:
                return True
            else:
                return False
        else:
            return True  

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("n"+self.outputName, "I")
        if not Module.globalOptions["isData"] and self.storeWeights:
            self.out.branch(self.outputName+"_weight_reco_nominal","F")
            self.out.branch(self.outputName+"_weight_id_nominal","F")

            if self.doVariations:
                self.out.branch(self.outputName+"_weight_reco_up","F")
                self.out.branch(self.outputName+"_weight_reco_down","F")
                self.out.branch(self.outputName+"_weight_id_up","F")
                self.out.branch(self.outputName+"_weight_id_down","F")

        for variable in self.storeKinematics:
            self.out.branch(self.outputName+"_"+variable,"F",lenVar="n"+self.outputName)


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        electrons = self.inputCollection(event)
        muons = Collection(event, "Muon")
        triggerObjects = self.triggerObjectCollection(event)

        selectedElectrons = []
        unselectedElectrons = []
        
        weight_reco_nominal = 1.
        weight_id_nominal = 1.

        if self.doVariations:
            weight_reco_up = 1.
            weight_reco_down = 1.
            weight_id_up = 1.
            weight_id_down = 1.

        for electron in electrons:
            # https://twiki.cern.ch/twiki/bin/view/CMS/CutBasedElectronIdentificationRun2
            if electron.pt>self.electronMinPt \
            and math.fabs(electron.eta)<self.electronMaxEta \
            and self.electronID(electron)\
            and self.triggerMatched(electron, triggerObjects):

                dxy = math.fabs(electron.dxy)
                dz = math.fabs(electron.dz)
                
                if math.fabs(electron.eta) < 1.479 and (dxy>0.05 or dz>0.10):
                    unselectedElectrons.append(electron)
                    continue
                elif dxy>0.10 or dz>0.20:
                    unselectedElectrons.append(electron)
                    continue

                #reject electron if close-by muon
                if len(muons)>0:
                    mindr = min(map(lambda muon: deltaR(muon, electron), muons))
                    if mindr < 0.05:
                        unselectedElectrons.append(electron)
                        continue

                selectedElectrons.append(electron)
                
                if not Module.globalOptions["isData"] and self.storeWeights:

                    weight_reco,weight_reco_err = getSFXY(self.electronRecoSFHist,electron.eta,electron.pt)
                    weight_id,weight_id_err = getSFXY(self.electronIdSF,electron.eta,electron.pt)

                    weight_reco_nominal *= weight_reco
                    weight_id_nominal *= weight_id

                    if self.doVariations:
                        weight_reco_up *=  weight_reco+weight_reco_err
                        weight_reco_down *= weight_reco-weight_reco_err
                        weight_id_up *=  weight_id+weight_id_err
                        weight_id_down *= weight_id-weight_id_err
                
            else:
                unselectedElectrons.append(electron)

        
        if not Module.globalOptions["isData"] and self.storeWeights:
            
            self.out.fillBranch(self.outputName+"_weight_reco_nominal", weight_reco_nominal)
            self.out.fillBranch(self.outputName+"_weight_id_nominal",weight_id_nominal)

            if self.doVariations:
                self.out.fillBranch(self.outputName+"_weight_reco_up", weight_reco_up)
                self.out.fillBranch(self.outputName+"_weight_reco_down", weight_reco_down)
                self.out.fillBranch(self.outputName+"_weight_id_up",weight_id_up)
                self.out.fillBranch(self.outputName+"_weight_id_down",weight_id_down)

        self.out.fillBranch("n"+self.outputName,len(selectedElectrons))

        for variable in self.storeKinematics:
            self.out.fillBranch(self.outputName+"_"+variable,map(lambda electron: getattr(electron,variable), selectedElectrons))

        setattr(event,self.outputName,selectedElectrons)
        setattr(event,self.outputName+"_unselected",unselectedElectrons)

        return True
