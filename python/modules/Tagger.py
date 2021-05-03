import os
import sys
import math
import json
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaR, deltaPhi


class Tagger(Module):
    def __init__(self,
            inputCollection=lambda event: Collection(event, 'Jet'),
            TagOutputName = 'BJet',
            NonTagOutputName = 'NonBJet',
            storeKinematics = ['mass', 'pt', 'eta', 'phi'],
            taggerFct = lambda obj: obj.btagDeepFlavB > 0.7,
                ):
        self.inputCollection = inputCollection
        self.TagOutputName = TagOutputName
        self.NonTagOutputName = NonTagOutputName
        self.storeKinematics = storeKinematics
        self.taggerFct = taggerFct


    def beginJob(self):
        pass


    def endJob(self):
        pass


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch('n'+self.TagOutputName, 'I')
        self.out.branch('n'+self.NonTagOutputName, 'I')

        for variable in self.storeKinematics:
            self.out.branch(self.TagOutputName + '_' + variable, 'F', lenVar='n'+self.TagOutputName)
            self.out.branch(self.NonTagOutputName + '_' + variable, 'F', lenVar='n'+self.NonTagOutputName)


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        tag = []
        Nontag = []

        # apply tagging
        for obj in self.inputCollection(event):
            if self.taggerFct(obj):
                tag.append(obj)
            else:
                Nontag.append(obj)


        # save output
        self.out.fillBranch('n'+self.TagOutputName, len(tag))
        self.out.fillBranch('n'+self.NonTagOutputName, len(Nontag))

        for variable in self.storeKinematics:
            self.out.fillBranch(self.TagOutputName + '_' + variable, map(lambda obj: getattr(obj, variable), tag))
            self.out.fillBranch(self.NonTagOutputName + '_' + variable, map(lambda obj: getattr(obj, variable), Nontag))

        return True
