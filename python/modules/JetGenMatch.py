from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from gen_helper import *



class JetGenMatchProducer(Module):
    def __init__(self, dRmax, JetCollection='Jet', GenCollection='GenPart'):
        self.dRmax = dRmax
        self.JetCollection = JetCollection
        self.GenCollection = GenCollection

        # branches to add
        self.MatchIDName = self.JetCollection + '_' + self.GenCollection + '_idx'
        self.pdgIdName = self.JetCollection + '_pdgId'
        self.chargeName = self.JetCollection + '_GenCharge'

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch(self.MatchIDName, "I", lenVar='n' + self.JetCollection)
        self.out.branch(self.pdgIdName, "I", lenVar='n' + self.JetCollection)
        self.out.branch(self.chargeName, "F", lenVar='n' + self.JetCollection)




    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        gen = Collection(event, self.GenCollection)
        jets = Collection(event, self.JetCollection)


        idx = []
        pdgid = []
        charge= []

        for jet in jets:
            dRmin = 999
            bestIdx = -1

            for i, gpart in enumerate(gen):
                # only match final state quarks and gluons
                if abs(gpart.pdgId) < 10 and isLastCopy(gpart):
                    dR = gpart.p4().DeltaR(jet.p4())

                    if dR < dRmin:
                        dRmin = dR
                        bestIdx = i


            if dRmin < self.dRmax:
                idx.append(bestIdx)
                pdgid.append(gen[bestIdx].pdgId)
                charge.append(getChargeFromPDG(gen[bestIdx]))
            else:
                idx.append(-1)
                pdgid.append(0)
                charge.append(0)


        self.out.fillBranch(self.MatchIDName, idx)
        self.out.fillBranch(self.pdgIdName, pdgid)
        self.out.fillBranch(self.chargeName, charge)

        return True
