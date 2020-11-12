from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True


import numpy

class ChargeSmearProducer(Module):
    def __init__(self, chargeBranch, outputName=None, efficiency=1, seed=12345):
        numpy.random.seed(seed=seed)

        if efficiency < 0 or efficiency > 1:
            print('INVALID efficiency "{}" given to ChargeSmearProducer. DISABLED'.format(efficiency))
            self.efficiency = 1
        else:
            self.efficiency = efficiency


        self.chargeBranch = chargeBranch
        if outputName==None:
            self.outputName = chargeBranch + '_smeared'
        else:
            self.outputName = outputName



    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch(self.outputName, "F")




    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass




    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        charge = getattr(event, self.chargeBranch)

        if not numpy.random.random() < self.efficiency:
            charge = -charge



        self.out.fillBranch(self.outputName, charge)

        return True
