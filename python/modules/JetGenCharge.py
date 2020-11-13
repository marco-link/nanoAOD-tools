from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from gen_helper import *



class JetGenChargeProducer(Module):
    def __init__(self, JetCollectionName='Jet', outputname='GenCharge'):
        self.JetCollectionName = JetCollectionName

        self.chargeName = self.JetCollectionName + '_' + outputname

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch(self.chargeName, "F", lenVar='n' + self.JetCollectionName)


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        jets = Collection(event, self.JetCollectionName)

        charge= []

        for jet in jets:
            flavour = getattr(jet, 'partonFlavour')
            if flavour == 21:
                charge.append(0)
            else:
                pdg = genDummy
                pdg.pdgId = flavour

                charge.append(getChargeFromPDG(pdg))


        self.out.fillBranch(self.chargeName, charge)

        return True
