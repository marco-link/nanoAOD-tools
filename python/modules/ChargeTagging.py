import os
import sys
import math
import json
import ROOT
import random
import numpy as np
import time
import imp

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class ChargeTagging(Module):

    def __init__(
        self,
        modelPath,
        featureDictFile,
        inputCollections = [lambda event: Collection(event, "Jet")],
        taggerName = "nn",
        globalOptions = {"isData":False},
    ):
        self.modelPath = os.path.expandvars(modelPath)
        
        self.inputCollections = inputCollections
        
        feature_dict_module = imp.load_source(
            'feature_dict',
            os.path.expandvars(featureDictFile)
        )
        
        self.featureDict = feature_dict_module.featureDict
        self.predictionLabels = feature_dict_module.predictionLabels
        
        self.taggerName = taggerName
        self.globalOptions = globalOptions

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.setup(inputTree)

        self.out.branch('n'+self.taggerName,"I")
        self.out.branch(self.taggerName+"_Bm","F",lenVar="n"+self.taggerName)
        self.out.branch(self.taggerName+"_B0bar","F",lenVar="n"+self.taggerName)
        self.out.branch(self.taggerName+"_B0","F",lenVar="n"+self.taggerName)
        self.out.branch(self.taggerName+"_Bp","F",lenVar="n"+self.taggerName)

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
                try:
                    global_jet_index = jetglobal_indices.index(jet._index)
                except ValueError:
                    print "WARNING: jet (pt: %s, eta: %s) does not have a matching global jet --> tagger cannot be evaluated!" % (jet.pt, jet.eta)
                    continue
                else:
                    global_jet = jetglobal[global_jet_index]
                    if abs(jet.eta - global_jet.eta) > 0.01 or \
                       abs(jet.phi - global_jet.phi) > 0.01:
                           print "Warning ->> jet might be mismatched!"
                    jetOriginIndices.add(global_jet_index)
                    setattr(jet, "globalIdx", global_jet_index)

        if event._tree._ttreereaderversion > self._ttreereaderversion:
            self.setup(event._tree)
        if len(jetOriginIndices)==0:
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

        #NOTE: take just first collection for quick study
        jets = self.inputCollections[0](event)
        probBm = [0.]*len(jets)
        probB0bar = [0.]*len(jets)
        probB0 = [0.]*len(jets)
        probBp = [0.]*len(jets)
        
        for ijet, jet in enumerate(jets):
            if hasattr(jet, "globalIdx"):     
                probBm[ijet] = predictionsPerIndex[jet.globalIdx][0]
                probB0bar[ijet] = predictionsPerIndex[jet.globalIdx][1]
                probB0[ijet] = predictionsPerIndex[jet.globalIdx][2]
                probBp[ijet] = predictionsPerIndex[jet.globalIdx][3]
        
        self.out.fillBranch('n'+self.taggerName,len(jets))
        self.out.fillBranch(self.taggerName+"_Bm",probBm)
        self.out.fillBranch(self.taggerName+"_B0bar",probB0bar)
        self.out.fillBranch(self.taggerName+"_B0",probB0)
        self.out.fillBranch(self.taggerName+"_Bp",probBp)
        
        
        return True
