import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import getGraph, getHist, combineHist2D, getSFXY, deltaR

class MuonSelection(Module):
    VERYTIGHT = 0
    TIGHT = 1
    MEDIUM = 2
    LOOSE = 3
    NONE = 4
    INV = 5

    def __init__(
        self,
        inputCollection=lambda event: Collection(event, "Muon"),
        outputName="tightMuons",
        triggerMatch=False,
        muonID=TIGHT,
        muonIso=TIGHT,
        muonMinPt=25.,
        muonMaxEta=2.4,
        storeKinematics=['pt','eta', 'pfRelIso04_all', 'tightId'],
        storeWeights=False,
        doVariations=True,
        additionalSyst=False,
    ):
        
        self.inputCollection = inputCollection
        self.outputName = outputName
        self.muonMinPt = muonMinPt
        self.muonMaxEta = muonMaxEta
        self.storeKinematics = storeKinematics
        self.storeWeights = storeWeights
        self.triggerMatch = triggerMatch
        self.doVariations = doVariations
        self.additionalSyst = additionalSyst

        if muonID!=MuonSelection.TIGHT or (muonIso!=MuonSelection.VERYTIGHT and muonIso!=MuonSelection.INV):
            raise Exception("Unsupported ID or ISO")

        self.triggerObjectCollection = lambda event: Collection(event, "TrigObj") if triggerMatch else lambda event: []

        if Module.globalOptions["year"] == '2016preVFP':

            self.idTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2016preVFP_UL/Efficiencies_muon_generalTracks_Z_Run2016_UL_HIPM_ID.root",
                "NUM_TightID_DEN_TrackerMuons_abseta_pt_syst"
            )
            
            self.isoVeryTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2016preVFP_UL/NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt.root",
                "NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt_syst"
            )

            self.muonRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2016preVFP_UL/Efficiency_muon_generalTracks_Run2016preVFP_UL_trackerMuon.root",
                "NUM_TrackerMuons_DEN_genTracks"
            )

        elif Module.globalOptions["year"] == '2016':

            self.idTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2016postVFP_UL/Efficiencies_muon_generalTracks_Z_Run2016_UL_ID.root",
                "NUM_TightID_DEN_TrackerMuons_abseta_pt_syst"
            )
            
            self.isoVeryTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2016postVFP_UL/NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt.root",
                "NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt_syst"
            )

            self.muonRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2016postVFP_UL/Efficiency_muon_generalTracks_Run2016postVFP_UL_trackerMuon.root",
                "NUM_TrackerMuons_DEN_genTracks"
            )

        elif Module.globalOptions["year"] == '2017':

            self.idTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2017_UL/Efficiencies_muon_generalTracks_Z_Run2017_UL_ID.root",
                "NUM_TightID_DEN_TrackerMuons_abseta_pt_syst"
            )
            
            self.isoVeryTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2017_UL/NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt.root",
                "NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt_syst"
            )

            self.muonRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2017_UL/Efficiency_muon_generalTracks_Run2017_UL_trackerMuon.root",
                "NUM_TrackerMuons_DEN_genTracks"
            )


        elif Module.globalOptions["year"] == '2018':

            self.idTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2018_UL/Efficiencies_muon_generalTracks_Z_Run2018_UL_ID.root",
                "NUM_TightID_DEN_TrackerMuons_abseta_pt_syst"
            )
            
            self.isoVeryTightSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2018_UL/NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt.root",
                "NUM_VeryTightRelIso_DEN_TightIDandIPCut_abseta_pt_syst"
            )

            self.muonRecoSFHist = getHist(
                "PhysicsTools/NanoAODTools/data/muon/2018_UL/Efficiency_muon_generalTracks_Run2018_UL_trackerMuon.root",
                "NUM_TrackerMuons_DEN_genTracks"
            )

        else:
            raise Exception("Error - invalid year for muon efficiencies")


        if muonID==MuonSelection.TIGHT:
            self.muonIdFct = lambda muon: muon.tightId==1
            self.muonIdSF = self.idTightSFHist
        else:
            raise Exception("Error - unsupported muon ID")

        if muonIso==MuonSelection.VERYTIGHT:
            self.muonIsoFct = lambda muon: muon.pfRelIso04_all<0.06
            if muonID==MuonSelection.TIGHT:
                self.muonIsoSF = self.isoVeryTightSFHist
            else:
                raise Exception("Error - unsupported muon ID/iso combination")

        elif muonIso==MuonSelection.INV:
            self.muonIsoFct = lambda muon: muon.pfRelIso04_all>0.25 and muon.pfRelIso04_all<0.8
            self.storeWeights = False

        else:
            raise Exception("Error - unsupported muon Iso")
        

    def triggerMatched(self, muon, trigger_object):
        if self.triggerMatch:
            trig_deltaR = math.pi
            for trig_obj in trigger_object:
                if abs(trig_obj.id) != 13:
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

        for variable in self.storeKinematics:
            self.out.branch(self.outputName+"_"+variable,"F",lenVar="n"+self.outputName)
            
        if not Module.globalOptions["isData"] and self.storeWeights:
            self.out.branch(self.outputName+"_weight_reco_nominal","F")
            self.out.branch(self.outputName+"_weight_id_nominal","F")
            self.out.branch(self.outputName+"_weight_iso_nominal","F")
            if self.doVariations:
                self.out.branch(self.outputName+"_weight_reco_up","F")
                self.out.branch(self.outputName+"_weight_reco_down","F")
                self.out.branch(self.outputName+"_weight_id_up","F")
                self.out.branch(self.outputName+"_weight_id_down","F")
                self.out.branch(self.outputName+"_weight_iso_up","F")
                self.out.branch(self.outputName+"_weight_iso_down","F")
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
        
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        muons = self.inputCollection(event)

        triggerObjects = self.triggerObjectCollection(event)

        selectedMuons = []
        unselectedMuons = []
        
        weight_reco_nominal = 1.
        weight_id_nominal = 1.
        weight_iso_nominal = 1.

        if self.doVariations:
            weight_reco_up = 1.
            weight_reco_down = 1.
            weight_id_up = 1.
            weight_id_down = 1.
            weight_iso_up = 1.
            weight_iso_down = 1.
        
        #https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideMuonIdRun2#Tight_Muon
        for muon in muons:
            if muon.pt>self.muonMinPt \
            and math.fabs(muon.eta)<self.muonMaxEta \
            and self.muonIdFct(muon) \
            and self.muonIsoFct(muon) \
            and self.triggerMatched(muon, triggerObjects):
            
                selectedMuons.append(muon)

                if not Module.globalOptions["isData"] and self.storeWeights:

                    weight_reco,weight_reco_err = getSFXY(self.muonRecoSFHist,abs(muon.eta),muon.pt)
                    weight_id,weight_id_err = getSFXY(self.muonIdSF,abs(muon.eta),muon.pt)
                    weight_iso,weight_iso_err = getSFXY(self.muonIsoSF,abs(muon.eta),muon.pt)

                    weight_reco_nominal *= weight_reco
                    weight_id_nominal *= weight_id
                    weight_iso_nominal *= weight_iso

                    if self.doVariations:
                        if self.additionalSyst:
                            weight_iso_err = (weight_iso_err**2+.005**2)**.5 # additional 0.5% flat uncertainty

                        weight_reco_up *=  weight_reco+weight_reco_err
                        weight_reco_down *= weight_reco-weight_reco_err
                        weight_id_up *=  weight_id+weight_id_err
                        weight_id_down *= weight_id-weight_id_err
                        weight_iso_up *=  weight_iso+weight_iso_err
                        weight_iso_down *= weight_iso-weight_iso_err

            else:
                unselectedMuons.append(muon)


        self.out.fillBranch("n"+self.outputName,len(selectedMuons))
        for variable in self.storeKinematics:
            self.out.fillBranch(self.outputName+"_"+variable,map(lambda muon: getattr(muon,variable),selectedMuons))
        
        if not Module.globalOptions["isData"] and self.storeWeights:
            self.out.fillBranch(self.outputName+"_weight_reco_nominal", weight_reco_nominal)
            self.out.fillBranch(self.outputName+"_weight_id_nominal", weight_id_nominal)
            self.out.fillBranch(self.outputName+"_weight_iso_nominal", weight_iso_nominal)

            if self.doVariations:
                self.out.fillBranch(self.outputName+"_weight_reco_up", weight_reco_up)
                self.out.fillBranch(self.outputName+"_weight_reco_down", weight_reco_down)
                self.out.fillBranch(self.outputName+"_weight_id_up", weight_id_up)
                self.out.fillBranch(self.outputName+"_weight_id_down", weight_id_down)
                self.out.fillBranch(self.outputName+"_weight_iso_up", weight_iso_up)
                self.out.fillBranch(self.outputName+"_weight_iso_down", weight_iso_down)

        setattr(event,self.outputName,selectedMuons)
        setattr(event,self.outputName+"_unselected",unselectedMuons)

        return True

