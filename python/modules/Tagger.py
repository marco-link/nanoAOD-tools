import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaR, deltaPhi


class TagJetProducer(Module):
    def __init__(self,
                 JetCollectionName = 'Jet',
                 TagJetOutputName = 'BJet',
                 NonTagJetOutputName = 'NonBJet',
                 storeVariables = ['mass', 'pt', 'eta', 'phi'],
                 tagger = 'btagDeepFlavB',
                 WP = -1):

        self.JetCollectionName = JetCollectionName
        self.TagJetOutputName = TagJetOutputName
        self.NonTagJetOutputName = NonTagJetOutputName
        self.storeVariables = storeVariables
        self.tagger = tagger
        self.WP = WP


    def beginJob(self):
        pass


    def endJob(self):
        pass


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch('n'+self.TagJetOutputName, 'I')
        self.out.branch('n'+self.NonTagJetOutputName, 'I')

        for variable in self.storeVariables:
            self.out.branch(self.TagJetOutputName + '_' + variable, 'F', lenVar='n'+self.TagJetOutputName)
            self.out.branch(self.NonTagJetOutputName + '_' + variable, 'F', lenVar='n'+self.NonTagJetOutputName)


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        jets = Collection(event, self.JetCollectionName)


        tagJets = []
        NontagJets = []


        # apply tagging
        for jet in jets:
            if getattr(jet, self.tagger) > self.WP:
                tagJets.append(jet)
            else:
                NontagJets.append(jet)


        # save output
        self.out.fillBranch('n'+self.TagJetOutputName, len(tagJets))
        self.out.fillBranch('n'+self.NonTagJetOutputName, len(NontagJets))

        for variable in self.storeVariables:
            self.out.fillBranch(self.TagJetOutputName + '_' + variable, map(lambda jet: getattr(jet, variable), tagJets))
            self.out.fillBranch(self.NonTagJetOutputName + '_' + variable, map(lambda jet: getattr(jet, variable), NontagJets))

        return True
