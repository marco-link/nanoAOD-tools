import os
import sys
import math
import json
import ROOT
import random
import numpy as np
import time
import imp
import feature_dict_module

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from utils import deltaPhi

class ChargeTagging(Module):

    def __init__(
        self,
        modelPath,
        inputCollections = [lambda event: Collection(event, "Jet")],
        filterJets = lambda jet: True,
        taggerName = "nn",
    ):
        self.modelPath = os.path.expandvars(modelPath)
        
        self.inputCollections = inputCollections
                
        self.featureDict = feature_dict_module.featureDict
        self.predictionLabels = feature_dict_module.predictionLabels
        
        self.filterJets = filterJets
        self.taggerName = taggerName

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.setup(inputTree)

    def setupTFEval(self,tree,modelFile):
        print "Building TFEval object"
        tfEval = ROOT.TFEval()
        print "Succesfully built TFEval object"

        if (not tfEval.loadGraph(modelFile)):
            sys.exit(1)
        tfEval.addOutputNodeName("prediction")
        print "--- Model: ",modelFile," ---"
        for groupName,featureCfg in self.featureDict.iteritems():
            if featureCfg.has_key("max"):
                print "building group ... %s, shape=[%i,%i], length=%s"%(groupName,featureCfg["max"],len(featureCfg["branches"]),featureCfg["length"])
                lengthBranch = ROOT.TFEval.createAccessor(tree.arrayReader(featureCfg["length"]))
                featureGroup = ROOT.TFEval.ArrayFeatureGroup(
                    groupName,
                    len(featureCfg["branches"]),
                    featureCfg["max"],
                    lengthBranch
                )
                for branchName in featureCfg["branches"]:
                    featureGroup.addFeature(ROOT.TFEval.createAccessor(tree.arrayReader(branchName)))
                tfEval.addFeatureGroup(featureGroup)
            else:
                print "building group ... %s, shape=[%i]"%(groupName,len(featureCfg["branches"]))
                featureGroup = ROOT.TFEval.ValueFeatureGroup(
                    groupName,
                    len(featureCfg["branches"])
                )
                for branchName in featureCfg["branches"]:
                    featureGroup.addFeature(ROOT.TFEval.createAccessor(tree.arrayReader(branchName)))
                tfEval.addFeatureGroup(featureGroup)

        return tfEval

    def setup(self,tree):
        self.tfEvalParametric = self.setupTFEval(tree,self.modelPath)
        print "setup model successfully..."

        self._ttreereaderversion = tree._ttreereaderversion


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):

        jetglobal = Collection(event, "global")
        jetglobal_indices = [global_jet.jetIdx for global_jet in jetglobal]

        jetOriginIndices = set() # superset of all indices to evaluate

        for jetCollection in self.inputCollections:
            jets = jetCollection(event)
            for ijet, jet in enumerate(jets):
                if not self.filterJets(jet):
                    continue    
                try:
                    global_jet_index = jetglobal_indices.index(jet._index)
                except ValueError:
                    print "ChargeTagging: WARNING: jet (pt: %s, eta: %s) does not have a matching global jet --> tagger cannot be evaluated!" % (jet.pt, jet.eta)
                    continue
                else:
                    global_jet = jetglobal[global_jet_index]
                    if math.fabs(jet.eta - global_jet.eta) > 0.01 or \
                       math.fabs(deltaPhi(jet.phi,global_jet.phi)) > 0.01:
                           print "ChargeTagging: Warning ->> jet might be mismatched!"
                    jetOriginIndices.add(global_jet_index)
                    setattr(jet, "globalIdx", global_jet_index)

        if event._tree._ttreereaderversion > self._ttreereaderversion:
            self.setup(event._tree)

        if len(jetOriginIndices)==0:
            for jetCollection in self.inputCollections:
                jets = jetCollection(event)
                for ijet, jet in enumerate(jets):
                    for ilabel,labelName in enumerate(self.predictionLabels):
                        resultDict[labelName] = -1.
                    setattr(jet,self.taggerName,resultDict)
            return True

        jetOriginIndices = list(jetOriginIndices)
        result = self.tfEvalParametric.evaluate(
            len(jetOriginIndices),
            np.array(jetOriginIndices,np.int64)
        )
        predictionsPerIndex={}
        for ijet,jetIndex in enumerate(jetOriginIndices):
            x = result.get("prediction",ijet)
            x = np.array(x)
            #apply softmax on logit output
            predictionsPerIndex[jetIndex] = np.exp(x)/sum(np.exp(x))

        for jetCollection in self.inputCollections:
            jets = jetCollection(event)
            for ijet, jet in enumerate(jets):
                resultDict = {}
                if hasattr(jet, "globalIdx"):
                    for ilabel,labelName in enumerate(self.predictionLabels):
                        resultDict[labelName] = predictionsPerIndex[jet.globalIdx][ilabel]
                else:
                    for ilabel,labelName in enumerate(self.predictionLabels):
                        resultDict[labelName] = -1.
                setattr(jet,self.taggerName,resultDict)

        return True
        
