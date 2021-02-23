import os
import sys
import math
import ROOT
import scipy.optimize

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module



class WbReconstruction(Module):
    def __init__(self,
                 bjetCollectionName = 'BJet',
                 WbosonCollectionName = 'Reco_w',
                 jetchargeName = 'charge',
                 outputName='Reco_wb'
                 ):
        self.bjetCollectionName = bjetCollectionName
        self.WbosonCollectionName = WbosonCollectionName
        self.jetchargeName = jetchargeName
        self.outputName=outputName


    def beginJob(self):
        pass


    def endJob(self):
        pass


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch(self.outputName + '_pt', 'F')
        self.out.branch(self.outputName + '_eta', 'F')
        self.out.branch(self.outputName + '_phi', 'F')
        self.out.branch(self.outputName + '_mass', 'F')

        self.out.branch(self.outputName + '_bjet_charge', 'F')


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def analyze(self, event):
        bjets = Collection(event, self.bjetCollectionName)
        W = Object(event, self.WbosonCollectionName)

        bjet = bjets[0] # TODO more clever bjet selection
        charge = getattr(bjet, self.jetchargeName)

        Wb = W.p4() + bjet.p4()


        self.out.fillBranch(self.outputName + '_pt', Wb.Pt())
        self.out.fillBranch(self.outputName + '_eta', Wb.Eta())
        self.out.fillBranch(self.outputName + '_phi', Wb.Phi())
        self.out.fillBranch(self.outputName + '_mass', Wb.M())

        self.out.fillBranch(self.outputName + '_bjet_charge', charge)

        return True
