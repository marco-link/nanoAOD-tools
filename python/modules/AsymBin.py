from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from gen_helper import *



class AsymBinProducer(Module):
    def __init__(self, massBranch, chargeBranch, outputName, mass=172.5, masswindow=20):
        self.massBranch = massBranch
        self.chargeBranch = chargeBranch

        self.outputName = outputName
        self.onshellName = self.outputName + '_IsOnShell'
        self.chargeName = self.outputName + '_ChargeSign'

        self.mass = mass
        self.masswindow = masswindow


    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch(self.onshellName, "I")
        self.out.branch(self.chargeName, "I")
        self.out.branch(self.outputName, "I")




    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def IsInWindow(self, m):
        if m < self.mass - self.masswindow:
            return  False
        elif m > self.mass + self.masswindow:
            return False

        return True



    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        asymBin = 0

        m = getattr(event, self.massBranch)
        charge = getattr(event, self.chargeBranch)
        onshell = self.IsInWindow(m)

        if charge < 0:
            asymBin = 1
            charge = -1
        elif charge > 0:
            asymBin = 2
            charge = 1
        else:
            charge = 0

        if not onshell:
            asymBin = -1 * asymBin


        self.out.fillBranch(self.onshellName, onshell)
        self.out.fillBranch(self.chargeName, int(charge))
        self.out.fillBranch(self.outputName, asymBin)

        return True
