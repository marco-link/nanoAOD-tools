import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class CalculateVariable(Module):
    def __init__(self, function, outputName, vartype='F', length=None):
        self.function = function
        self.outputName = outputName
        self.vartype = vartype
        self.length = length

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        if self.length is None:
            self.out.branch(self.outputName, self.vartype)
        else:
            self.out.branch(self.outputName, self.vartype, lenVar=self.length)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        self.out.fillBranch(self.outputName, self.function(event))

        return True
