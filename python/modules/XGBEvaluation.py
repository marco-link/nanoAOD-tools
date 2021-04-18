import os
import imp
import numpy as np
from xgboost import XGBClassifier, Booster, DMatrix
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class XGBEvaluation(Module):
    def __init__(
        self,
        modelPath="${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/bdt/201117/nominal/bdt_2016.model",
        inputFeatures="${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/bdt/201117/nominal/bdt_inputs.py",
        systematics=["nominal"],
        inputs=[],
        outputName ="bdt_score"
    ):
        self.modelPath = os.path.expandvars(modelPath)
        print "---","BDT model: ",self.modelPath
        self.systematics = systematics
        self.outputName = outputName
        
        feature_dict_module = imp.load_source(
            'features',
            os.path.expandvars(inputFeatures)
        )
        self.features = feature_dict_module.features
        print "[%i]"%len(self.features)," BDT features: ",map(lambda x: x[0],self.features)
       

    def beginJob(self):
        pass
        
    def endJob(self):
        pass
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.model = XGBClassifier()
        self.booster = Booster(model_file=self.modelPath)
        self.model._Booster = self.booster
        self.out = wrappedOutputTree
        for systematic in self.systematics:
            self.out.branch(self.outputName+"_"+systematic, "F")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):

        #TODO: XGB does not notice if wrong number of inputs is given

        featureArr = np.zeros((len(self.systematics),len(self.features)))
        for i, syst in enumerate(self.systematics):
            for j, (featureName, featureFct) in enumerate(self.features):
                featureArr[i,j] = featureFct(event,syst)
        
        #print featureArr

        bdt_score = self.model.predict_proba(featureArr)
        #print bdt_score

        for i, syst in enumerate(self.systematics):
            self.out.fillBranch(self.outputName+"_"+syst,bdt_score[i, 1])

        return True
