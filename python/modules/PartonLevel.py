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

        self.out.branch('npartonLevel_W', "I")
        self.out.branch('partonLevel_W_charge', "I", lenVar='npartonLevel_W')
        self.out.branch('partonLevel_W_pt', "F", lenVar='npartonLevel_W')
        self.out.branch('partonLevel_W_eta', "F", lenVar='npartonLevel_W')
        self.out.branch('partonLevel_W_phi', "F", lenVar='npartonLevel_W')
        self.out.branch('partonLevel_W_mass', "F", lenVar='npartonLevel_W')

        self.out.branch("partonLevel_Wdau_pt", "F", 2)
        self.out.branch("partonLevel_Wdau_eta", "F", 2)
        self.out.branch("partonLevel_Wdau_phi", "F", 2)
        self.out.branch("partonLevel_Wdau_mass", "F", 2)
        self.out.branch("partonLevel_Wdau_pdgId", "I", 2)

        self.out.branch('npartonLevel_bquarks', 'I')
        self.out.branch('partonLevel_bquarks_pt', "F", lenVar='npartonLevel_bquarks')
        self.out.branch('partonLevel_bquarks_eta', "F", lenVar='npartonLevel_bquarks')
        self.out.branch('partonLevel_bquarks_phi', "F", lenVar='npartonLevel_bquarks')
        self.out.branch('partonLevel_bquarks_mass', "F", lenVar='npartonLevel_bquarks')
        self.out.branch('partonLevel_bquarks_charge', "I", lenVar='npartonLevel_bquarks')

        self.out.branch('npartonLevel_bFromTop', 'I')
        self.out.branch('partonLevel_bFromTop_pt', "F", lenVar='npartonLevel_bFromTop')
        self.out.branch('partonLevel_bFromTop_eta', "F", lenVar='npartonLevel_bFromTop')
        self.out.branch('partonLevel_bFromTop_phi', "F", lenVar='npartonLevel_bFromTop')
        self.out.branch('partonLevel_bFromTop_mass', "F", lenVar='npartonLevel_bFromTop')
        self.out.branch('partonLevel_bFromTop_charge', "I", lenVar='npartonLevel_bFromTop')

        self.out.branch('partonLevel_top_pt', "F")
        self.out.branch('partonLevel_top_eta', "F")
        self.out.branch('partonLevel_top_phi', "F")
        self.out.branch('partonLevel_top_mass', "F")


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        genParticles = Collection(event,"GenPart")

        w_idx = None
        wdaus = []
        bquarks = []
        top_idx = None
        top = None
        b_from_top = None

        for idx, particle in enumerate(genParticles):
            if not (fromHardProcess(particle)):
                continue

            # skip initial partons
            if particle.status == 21:
                continue

            # furthermore, skip also particles that appear out of nowhere
            if particle.genPartIdxMother == -1:
                continue

            if abs(particle.pdgId)==24 and isLastCopy(particle):
                if w_idx != None:
                    print("WARNING - multiple W boson at parton level")
                w_idx = idx

            if particle.genPartIdxMother == w_idx:
                wdaus.append(particle)

            if abs(particle.pdgId)==5 and isLastCopy(particle):
                bquarks.append(particle)

            if abs(particle.pdgId)==6 and isLastCopy(particle):
                if top!=None:
                    print "WARNING - multiple tops at gen level"
                top_idx = idx
                top = particle

            if particle.genPartIdxMother == top_idx and abs(particle.pdgId)==5:
                b_from_top = particle

        wboson = genDummy()
        if w_idx != None:
            wboson = genParticles[w_idx]

        if len(wdaus) < 2:
            print("WARNING - Wbau not found")
            wdaus.append(genDummy())

        if len(bquarks) == 1:
            bquarks = [genDummy()]
        bquarks = sorted(bquarks,key=lambda x: x.pt, reverse=True)

        if top == None:
            top = genDummy()
            b_from_top = [genDummy()]
        else:
            b_from_top = [b_from_top]


        self.out.fillBranch('npartonLevel_W', 1)
        self.out.fillBranch('partonLevel_W_charge', map(lambda w: getChargeFromPDG(w), [wboson]))
        self.out.fillBranch('partonLevel_W_pt', map(lambda w: w.pt, [wboson]))
        self.out.fillBranch('partonLevel_W_eta', map(lambda w: w.eta, [wboson]))
        self.out.fillBranch('partonLevel_W_phi', map(lambda w: w.phi, [wboson]))
        self.out.fillBranch('partonLevel_W_mass', map(lambda w: w.mass, [wboson]))

        self.out.fillBranch('partonLevel_Wdau_pt', map(lambda wdau: wdau.pt, wdaus))
        self.out.fillBranch('partonLevel_Wdau_eta', map(lambda wdau: wdau.eta, wdaus))
        self.out.fillBranch('partonLevel_Wdau_phi', map(lambda wdau: wdau.phi, wdaus))
        self.out.fillBranch('partonLevel_Wdau_mass', map(lambda wdau: wdau.mass, wdaus))
        self.out.fillBranch('partonLevel_Wdau_pdgId', map(lambda wdau: wdau.pdgId, wdaus))


        def bquarkcharge(quark):
            c = getChargeFromPDG(quark)
            if c > 0:
                return 1
            elif c < 0:
                return -1
            else:
                return 0

        self.out.fillBranch('npartonLevel_bquarks', len(bquarks))
        self.out.fillBranch('partonLevel_bquarks_pt', map(lambda quark: quark.pt, bquarks))
        self.out.fillBranch('partonLevel_bquarks_eta', map(lambda quark: quark.eta, bquarks))
        self.out.fillBranch('partonLevel_bquarks_phi', map(lambda quark: quark.phi, bquarks))
        self.out.fillBranch('partonLevel_bquarks_mass', map(lambda quark: quark.mass, bquarks))
        self.out.fillBranch('partonLevel_bquarks_charge', map(lambda quark: bquarkcharge(quark), bquarks))

        self.out.fillBranch('npartonLevel_bFromTop', len(b_from_top))
        self.out.fillBranch('partonLevel_bFromTop_pt', map(lambda quark: quark.pt, b_from_top))
        self.out.fillBranch('partonLevel_bFromTop_eta', map(lambda quark: quark.eta, b_from_top))
        self.out.fillBranch('partonLevel_bFromTop_phi', map(lambda quark: quark.phi, b_from_top))
        self.out.fillBranch('partonLevel_bFromTop_mass', map(lambda quark: quark.mass, b_from_top))
        self.out.fillBranch('partonLevel_bFromTop_charge', map(lambda quark: bquarkcharge(quark), b_from_top))

        self.out.fillBranch('partonLevel_top_pt', top.pt)
        self.out.fillBranch('partonLevel_top_eta', top.eta)
        self.out.fillBranch('partonLevel_top_phi', top.phi)
        self.out.fillBranch('partonLevel_top_mass', top.mass)


        return True
