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

        self.out.branch('particleLevel_met_pt', "F")
        self.out.branch('particleLevel_met_phi', "F")

        self.out.branch('particleLevel_lepton_pdgId', "I")
        self.out.branch('particleLevel_lepton_charge', "I")
        self.out.branch('particleLevel_lepton_pt', "F")
        self.out.branch('particleLevel_lepton_eta', "F")
        self.out.branch('particleLevel_lepton_phi', "F")
        self.out.branch('particleLevel_lepton_mass', "F")

        self.out.branch('nparticleLevel_bjets', 'I')
        self.out.branch('particleLevel_bjets_pt', "F", lenVar='nparticleLevel_bjets')
        self.out.branch('particleLevel_bjets_eta', "F", lenVar='nparticleLevel_bjets')
        self.out.branch('particleLevel_bjets_phi', "F", lenVar='nparticleLevel_bjets')
        self.out.branch('particleLevel_bjets_mass', "F", lenVar='nparticleLevel_bjets')
        self.out.branch('particleLevel_bjets_charge', "I", lenVar='nparticleLevel_bjets')

        self.out.branch('nparticleLevel_ljets', 'I')
        self.out.branch('particleLevel_ljets_pt', "F", lenVar='nparticleLevel_ljets')
        self.out.branch('particleLevel_ljets_eta', "F", lenVar='nparticleLevel_ljets')
        self.out.branch('particleLevel_ljets_phi', "F", lenVar='nparticleLevel_ljets')
        self.out.branch('particleLevel_ljets_mass', "F", lenVar='nparticleLevel_ljets')



    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def analyze(self, event):

        # MET

        met = Object(event,"MET")
        genMet = ROOT.TLorentzVector()
        genMet.SetPtEtaPhiM(met.fiducialGenPt, 0., met.fiducialGenPhi, 0.)

        self.out.fillBranch('particleLevel_met_pt', met.fiducialGenPt)
        self.out.fillBranch('particleLevel_met_phi', met.fiducialGenPhi)


        # lepton

        leptons = sorted(Collection(event,"GenDressedLepton"), key=lambda x: x.pt, reverse=True)

        if len(leptons) < 1:
            leptons = [genDummy()]

        lepton = leptons[0]
        self.out.fillBranch('particleLevel_lepton_pdgId', lepton.pdgId)
        self.out.fillBranch('particleLevel_lepton_charge', int(getChargeFromPDG(lepton)))
        self.out.fillBranch('particleLevel_lepton_pt', lepton.pt)
        self.out.fillBranch('particleLevel_lepton_eta', lepton.eta)
        self.out.fillBranch('particleLevel_lepton_phi', lepton.phi)
        self.out.fillBranch('particleLevel_lepton_mass', lepton.mass)



        # jets

        ljets = []
        bjets = []

        for jet in Collection(event,"GenJet"):
            if lepton and deltaR(jet, lepton)<0.4:
                continue

            if abs(jet.hadronFlavour)==5 and jet.pt>30 and math.fabs(jet.eta)<2.4:
                bjets.append(jet)
            elif jet.pt>30 and math.fabs(jet.eta)<4.7:
                ljets.append(jet)


        if len(bjets) == 0:
            print('no bjets found @particleLevel')
            bjets = [genDummy()]
            bjets[0].partonFlavour = 0

        #note: hadronflavour does not store the sign
        def bjetcharge(bjet):
            if bjet.partonFlavour==5:
                return -1 #b
            elif bjet.partonFlavour==-5:
                return 1 #bbar
            else:
                return 0

        self.out.fillBranch('nparticleLevel_bjets', len(bjets))
        self.out.fillBranch('particleLevel_bjets_pt', map(lambda jet: jet.pt, bjets))
        self.out.fillBranch('particleLevel_bjets_eta', map(lambda jet: jet.eta, bjets))
        self.out.fillBranch('particleLevel_bjets_phi', map(lambda jet: jet.phi, bjets))
        self.out.fillBranch('particleLevel_bjets_mass', map(lambda jet: jet.mass, bjets))
        self.out.fillBranch('particleLevel_bjets_charge', map(lambda jet: bjetcharge(jet), bjets))


        self.out.fillBranch('nparticleLevel_ljets', len(ljets))
        self.out.fillBranch('particleLevel_ljets_pt', map(lambda jet: jet.pt, ljets))
        self.out.fillBranch('particleLevel_ljets_eta', map(lambda jet: jet.eta, ljets))
        self.out.fillBranch('particleLevel_ljets_phi', map(lambda jet: jet.phi, ljets))
        self.out.fillBranch('particleLevel_ljets_mass', map(lambda jet: jet.mass, ljets))

        return True
