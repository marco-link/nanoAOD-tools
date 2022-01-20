import uproot
import numpy as np
import scipy
import json
import os
import sys
import random
import sklearn
import sklearn.ensemble
import sklearn.metrics 
import sklearn.externals
import sklearn.model_selection
import argparse


import xgboost
import gc

import matplotlib
matplotlib.use('Agg')

from matplotlib import rcParams
#rcParams['font.sans-serif'] = ['Helvetica']
#rcParams['font.family'] = 'sans-serif'
rcParams['axes.labelsize'] = 'x-large'
rcParams['xtick.labelsize'] = 'large'
rcParams['ytick.labelsize'] = 'large'
rcParams['axes.titlesize'] = 'x-large'
rcParams['legend.fontsize'] = 'medium'
rcParams['grid.linewidth'] = 1.
rcParams['lines.linewidth'] = 1.5

import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--lr', dest='lr', type=float, default=0.1, help='learning rate')
parser.add_argument('--minsize', dest='minsize', type=float, default=0.05, help='min node size')
parser.add_argument('--depth', dest='depth', type=int, default=4, help='depth')
parser.add_argument('--bagging', dest='bagging', type=float, default=0.75, help='bagging')
parser.add_argument('--trees', dest='trees', type=int, default=250, help='trees')
parser.add_argument('output', nargs=1)
args = parser.parse_args()

outputName = args.output[0]

print "Learning rate",args.lr
print "Min size",args.minsize
print "Depth",args.depth
print "Number of trees:",args.trees
print "Bagging rate:",args.bagging
print "Output name",outputName


random.seed(123456)
np.random.seed(234567)

filePath = "/vols/cms/mkomm/ST/NANOX_210402/MC_2016"

xsecs = {

    # Drell-Yan + jets
    # NLO
    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SummaryTable1G25ns#DY_Z

    "DYJetsToLL_M-10to50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8-2016":18610,
    "DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8-2016":1921.8*3,
    
    "DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8-ext1-2016":1921.8*3,
    "DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8-ext2-2016":1921.8*3,
    "DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8-2017":1921.8*3,
    "DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8-2018": 1921.8*3,

    # QCD (multijet)


    #https://cms-pdmv.cern.ch/mcm/requests?page=-1&dataset_name=QCD_Pt_*to*_TuneCUETP8M1_13TeV_pythia8&member_of_campaign=RunIIFall14GS
    "QCD_Pt-1000toInf_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 1.621,
    "QCD_Pt-120to170_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 2.52E+04,
    "QCD_Pt-15to20_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 3819570.0,
    "QCD_Pt-170to300_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 8654.0,
    "QCD_Pt-20to30_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 2960198.0,
    "QCD_Pt-300to470_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 797.0,
    "QCD_Pt-30to50_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 1652471.0,
    "QCD_Pt-470to600_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 78.91,
    "QCD_Pt-50to80_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 4.38E+05,
    "QCD_Pt-600to800_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 25.095,
    "QCD_Pt-800to1000_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 4.707,
    "QCD_Pt-80to120_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016": 1.06E+05,

    "QCD_Pt-120to170_EMEnriched_TuneCUETP8M1_13TeV_pythia8-2016": 477000*0.132,
    "QCD_Pt-170to300_EMEnriched_TuneCUETP8M1_13TeV_pythia8-2016": 114000*0.165,
    "QCD_Pt-20to30_EMEnriched_TuneCUETP8M1_13TeV_pythia8-2016": 557600000*0.0096,
    "QCD_Pt-300toInf_EMEnriched_TuneCUETP8M1_13TeV_pythia8-2016": 9000*0.15,
    "QCD_Pt-30to50_EMEnriched_TuneCUETP8M1_13TeV_pythia8-2016": 136000000*0.073,
    "QCD_Pt-50to80_EMEnriched_TuneCUETP8M1_13TeV_pythia8-2016": 19800000*0.146,
    "QCD_Pt-80to120_EMEnriched_TuneCUETP8M1_13TeV_pythia8-2016": 2800000*0.125,


    # Single-top
    # https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopRefXsec#Single_top_t_channel_cross_secti
    # NLO
    "ST_t-channel_antitop_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8-2016": 80.95,
    "ST_t-channel_top_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1-2016": 136.02,
    "ST_tW_antitop_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M1-2016": 71.7/2.,
    "ST_tW_top_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M1-2016": 71.7/2.,

    # TTbar
    # https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO (mtop=172.5 GeV)


    "TTToSemiLeptonic_TuneCP5_PSweights_13TeV-powheg-pythia8-2016":365.3452,
    "TTTo2L2Nu_TuneCP5_PSweights_13TeV-powheg-pythia8-2016": 88.2877,

    "TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8-2016":831.,
    "TTJets_TuneCP5_13TeV-madgraphMLM-pythia8-2017":831.,
    "TTJets_TuneCP5_13TeV-madgraphMLM-pythia8-2018":831.,
    

    # W->l nu + jets
    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SummaryTable1G25ns
    # NLO
    "WToLNu_0J_13TeV-amcatnloFXFX-pythia8-ext1-2016": 49670.,
    "WToLNu_1J_13TeV-amcatnloFXFX-pythia8-2016": 8264.,
    "WToLNu_2J_13TeV-amcatnloFXFX-pythia8-ext4-2016": 3226.,
    
    

    # Z -> nu nu + jets
    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SummaryTable1G25ns
    # LO

    # Z -> nu nu + jets
    # MCM
    # NLO
    
    "WGToLNuG_TuneCUETP8M1_13TeV-madgraphMLM-pythia8-2016": 405.271,
    "ZGToLLG_01J_5f_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8-2016": 131.1,

    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV
    # NNLO
    "WW_TuneCUETP8M1_13TeV-pythia8": 118.7,

    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SummaryTable1G25ns#Diboson
    # NLO
    "WZ_TuneCUETP8M1_13TeV-pythia8": 47.13,
    "ZZ_TuneCUETP8M1_13TeV-pythia8": 16.523,
}


with open('/vols/cms/mkomm/ST/CMSSW_11_1_7/src/eventyields.json') as f:
    genweights = json.load(f)
    
processes = {
    #"DYJetsToLL_M-10to50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8-2016",
    "DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8-ext2-2016",
    
    #"QCD_Pt-1000toInf_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-120to170_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-15to20_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-170to300_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-20to30_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-300to470_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-30to50_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-470to600_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-50to80_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-600to800_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-800to1000_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    #"QCD_Pt-80to120_MuEnrichedPt5_TuneCUETP8M1_13TeV_pythia8-2016",
    
    "TTTo2L2Nu_TuneCP5_PSweights_13TeV-powheg-pythia8-2016",
    "TTToSemiLeptonic_TuneCP5_PSweights_13TeV-powheg-pythia8-2016",
    #"WToLNu_0J_13TeV-amcatnloFXFX-pythia8-ext1-2016",
    "WToLNu_1J_13TeV-amcatnloFXFX-pythia8-2016",
    "WToLNu_2J_13TeV-amcatnloFXFX-pythia8-ext4-2016"
}

inputs = [
    #"nnominal_selectedJets",
    #"nnominal_selectedBJets",
    
    "tightMuons_pt",
    "tightMuons_charge",
    
    "nominal_mtw",
    "nominal_met",
    "nominal_met_lepton_deltaPhi",
    "nominal_eventShape_C",
    
    "nominal_ljet_eta",
    "nominal_bjet_lepton_deta",
    "nominal_ljet_bjet_dR",
    "nominal_wboson_cosHelicity",
    "nominal_top_cosPolarization",
    
    "nominal_top_mass",
    "nominal_top_pt",
]

preprocs = {
    "tightMuons_pt": lambda x: x[:,0], 
    "tightMuons_charge": lambda x: x[:,0],
    
    "nominal_met_lepton_deltaPhi": lambda x: np.abs(x),
    "nominal_bjet_lepton_deta": lambda x: np.abs(x),
    "nominal_ljet_eta": lambda x: np.abs(x)
}


if not os.path.exists('trainData.npz'):
        
    dataList = []
    for process in processes:
        print "Reading ... ",process
        sumEvents = 0
        sumWeights = 0
        for f in os.listdir(os.path.join(filePath,process)):
            if f.endswith(".root"):
                rootFile = uproot.open(os.path.join(filePath,process,f))
                if not 'Friends;1' in rootFile.keys():
                    print 'skip file ',os.path.join(filePath,process,f)
                    continue
                tree = rootFile["Friends"]
                if len(tree)==0:
                    continue
                inputData = tree.arrays(inputs)
                
                njets = tree.array('nnominal_selectedJets')
                nbjets = tree.array('nnominal_selectedBJets')
                sel = (nbjets>0)*(njets>1)*(njets<4)
                
                if np.sum(1.*sel)<10:
                    continue
                
                for k in inputData.keys():
                    inputData[k] = inputData[k][sel]
                
                for k,fct in preprocs.items():
                    inputData[k] = fct(inputData[k])
                    
                featureArr = [inputData[k] for k in inputs]
                featureArr = np.stack(featureArr,axis=1)

                xsecArr = tree.array("genweight")[sel]/genweights[process]["weights"]*1000.*xsecs[process]
                
                if process.find("QCD")>=0:
                    xsecArr *= 1e-3
                
                xsecArr = xsecArr*(1-0.9*(xsecArr<0)) #reduce neg events
                
                dataList.append({"features":featureArr,"weight":xsecArr,"label":np.zeros(len(xsecArr))})
                sumEvents += xsecArr.shape[0]
                sumWeights += np.sum(xsecArr)
                #break
        if sumEvents>0:
            print " -> events/weights/eff = ",sumEvents,sumWeights,sumWeights/sumEvents
        else:
            print " -> events/weights/eff = -"

    sumEvents = 0
    sumWeights = 0  
    for process in os.listdir(os.path.join(filePath)):
        if process.startswith("ST_4f_w_lo-2016"):
            print "Reading ... ",process
            for f in os.listdir(os.path.join(filePath,process)):
                if f.endswith(".root"):
                    rootFile = uproot.open(os.path.join(filePath,process,f))
                    if not 'Friends;1' in rootFile.keys():
                        print 'skip file ',os.path.join(filePath,process,f)
                        continue
                    tree = rootFile["Friends"]
                    if len(tree)==0:
                        continue
                    inputData = tree.arrays(inputs)
                    
                    njets = tree.array('nnominal_selectedJets')
                    nbjets = tree.array('nnominal_selectedBJets')
                    sel = (nbjets>0)*(njets>1)*(njets<4)
                    
                    for k in inputData.keys():
                        inputData[k] = inputData[k][sel]
                    
                    for k,fct in preprocs.items():
                        inputData[k] = fct(inputData[k])
                        
                    featureArr = [inputData[k] for k in inputs]
                    featureArr = np.stack(featureArr,axis=1)
                    xsecArr = tree.array("genweight")[sel]/genweights[process]['1']['weights']*1000.*100 #assume 100pb as xsec for signal
                    
                    xsecArr = xsecArr*(1-0.9*(xsecArr<0)) #reduce neg events
                    
                    chargeCorrelation = tree.array('partonLevel_chargeCorrelation')[sel]
                    
                    #sum with bias
                    npos = 1.*np.sum(chargeCorrelation>0)+1
                    nneg = 1.*np.sum(chargeCorrelation<0)+1
                    
                    extraWeight = (chargeCorrelation>0)*(npos+nneg)/npos+(chargeCorrelation<0)*(npos+nneg)/nneg
                    #extraWeight = 1
                    
                    dataList.append({"features":featureArr,"weight":xsecArr*extraWeight,"label":np.ones(len(xsecArr))})
                    sumEvents += xsecArr.shape[0]
                    sumWeights += np.sum(xsecArr)
    print " -> events/weights/eff = ",sumEvents,sumWeights,sumWeights/sumEvents
            
    random.shuffle(dataList)

    #dataList = dataList[:100]

    featuresArr = []
    weightArr = []
    labelArr = []


    for data in dataList:
        featuresArr.append(data["features"])
        weightArr.append(data["weight"])
        labelArr.append(data["label"])

    del dataList
    gc.collect()
        
    featuresArr = np.concatenate(featuresArr,axis=0)
    weightArr = np.concatenate(weightArr,axis=0)
    labelArr = np.concatenate(labelArr,axis=0)



    print 'total samples',featuresArr.shape
    #use only 20% for training
    featuresArr,_,labelArr,_,weightArr,_ = sklearn.model_selection.train_test_split(
        featuresArr,labelArr,weightArr,test_size=0.8,shuffle=True, random_state=76177
    )

    np.savez_compressed('trainData.npz',features=featuresArr,labels=labelArr,weights=weightArr)
else:
    loaded = np.load('trainData.npz')
    featuresArr = loaded['features']
    labelArr = loaded['labels']
    weightArr = loaded['weights']


print 'split samples',featuresArr.shape

bkgSum = np.sum(weightArr[labelArr<0.5])
sigSum = np.sum(weightArr[labelArr>0.5])

print 'weight sum bkg/sig',bkgSum,sigSum
weightArr *= (labelArr<0.5)*labelArr.shape[0]/bkgSum+(labelArr>0.5)*labelArr.shape[0]/sigSum
print 'weight sum reweighted bkg/sig',np.sum(weightArr[labelArr<0.5]),np.sum(weightArr[labelArr>0.5])
#sys.exit(1)


trainFeatures,testFeatures,trainLabel,testLabel,trainWeight,testWeight = sklearn.model_selection.train_test_split(
    featuresArr,labelArr,weightArr,test_size=0.2,shuffle=True, random_state=24155
)


#### USE TEST=TRAIN for testing
testFeatures = trainFeatures
testLabel = trainLabel
testWeight = trainWeight

print "Train/test: ",trainFeatures.shape,testFeatures.shape

for i, inputName in enumerate(inputs):
    print inputName,trainFeatures[0:10,i]

del featuresArr,weightArr,labelArr
gc.collect()

bdt = xgboost.XGBClassifier(
     #loss='deviance', #=for logistic regression
     n_estimators=args.trees, 
     learning_rate=args.lr,
     max_depth=args.depth, 
     min_child_weight=np.sum(trainWeight)*args.bagging*args.minsize,
     use_label_encoder = False,
     verbose=2,
     objective='binary:logistic',
     n_jobs=1,
     subsample=args.bagging, 
     importance_type='gain',
     booster='gbtree',
     tree_method='approx', 
)

bdt.fit(
    trainFeatures, trainLabel, sample_weight=trainWeight, 
    eval_metric=["error", "logloss"], 
    eval_set=[(trainFeatures, trainLabel), (testFeatures, testLabel)], 
    sample_weight_eval_set = [trainWeight,testWeight],
    verbose=True
)
bdt._Booster.save_model(outputName+"_bdt.bin")

results = bdt.evals_result()

trainPred = bdt.predict_proba(trainFeatures)[:,1]
testPred = bdt.predict_proba(testFeatures)[:,1]
fprTrain, tprTrain, thresTrain = sklearn.metrics.roc_curve(trainLabel, trainPred)
fprTest, tprTest, thresTest = sklearn.metrics.roc_curve(testLabel, testPred)

predTrainBkg,predTrainBkgWeight = trainPred[trainLabel<0.5],trainWeight[trainLabel<0.5]/np.sum(trainWeight[trainLabel<0.5])
predTrainSig,predTrainSigWeight = trainPred[trainLabel>0.5],trainWeight[trainLabel>0.5]/np.sum(trainWeight[trainLabel>0.5])

predTestBkg,predTestBkgWeight = testPred[testLabel<0.5],testWeight[testLabel<0.5]/np.sum(testWeight[testLabel<0.5])
predTestSig,predTestSigWeight = testPred[testLabel>0.5],testWeight[testLabel>0.5]/np.sum(testWeight[testLabel>0.5])


aucTrain, aucTest = sklearn.metrics.auc(fprTrain, tprTrain), sklearn.metrics.auc(fprTest, tprTest)
accTrain = sklearn.metrics.accuracy_score(trainLabel, 1.*(trainPred>0.5), normalize=True, sample_weight=trainWeight)
accTest = sklearn.metrics.accuracy_score(testLabel, 1.*(testPred>0.5), normalize=True, sample_weight=testWeight)
print "AUC", aucTrain, aucTest
print "Accuracy", accTrain, accTest
                  
for bkgFrac in [0.3,0.2,0.1,0.05,0.01]:
    bkgIdx = np.argmin(np.abs(fprTest-bkgFrac))
    print "Bkg@%.0f%%: Sigeff=%.1f%%, Thres=%.3f"%(100.*bkgFrac,100.*tprTest[bkgIdx],thresTest[bkgIdx])
    
fstat = open(outputName+"_stat.dat",'w')
fstat.write("%.3e; %.3e; %.5f; %.5f; %.3f; %.3f \n"%(
    results['validation_0']['logloss'][-1],
    results['validation_1']['logloss'][-1],
    aucTrain, aucTest,
    100.*accTrain, 100.*accTest
))
fstat.close()

plt.figure(figsize=[7.3, 6.5])
plt.plot(np.arange(bdt.n_estimators),results['validation_0']['logloss'],color='darkgray',linewidth=2, linestyle='-',label='Train')
plt.plot(np.arange(bdt.n_estimators),results['validation_1']['logloss'],color='royalblue',linewidth=3, linestyle='--',label='Test')
plt.ylabel("log(Loss)")
plt.xlabel("#Estimators")
plt.tight_layout(rect=[0., 0, 1, 0.91])
plt.legend(ncol=2, bbox_to_anchor=(0, 1.0), loc="lower left")
plt.savefig(outputName+"_lr.pdf")
plt.close()

plt.figure(figsize=[7.3, 6.5])
plt.plot(tprTrain,fprTrain,color='darkgray',linewidth=2, linestyle='-',label="Train")
plt.plot(tprTest,fprTest,color='royalblue',linewidth=3, linestyle='--',label="Test")
bkgIdx = np.argmin(np.abs(fprTest-0.1))
plt.plot([tprTest[bkgIdx],tprTest[bkgIdx]],[1e-3,fprTest[bkgIdx]] ,color='black',linewidth=1, linestyle='-')
plt.xlim([0.0,1.0])
plt.ylim([1e-3,1.0])
plt.yscale('log')
plt.xlabel("Signal efficiency")
plt.ylabel("Background efficiency")
plt.gca().xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(5))
plt.gca().yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(5))
plt.grid(True, which='both', axis='both', color='black', linestyle='--', linewidth=1)
plt.tight_layout(rect=[0., 0, 1, 0.91])
plt.legend(ncol=2, bbox_to_anchor=(0, 1.0), loc="lower left")
plt.savefig(outputName+"_roc.pdf")
plt.close()



plt.figure(figsize=[7.3, 6.5])
plt.hist(predTrainBkg, bins=40, range=[0,1], histtype='stepfilled', color='royalblue', weights=predTrainBkgWeight,label="Train bkg", alpha=0.6)
plt.hist(predTrainSig, bins=40, range=[0,1], histtype='stepfilled', color='orange', weights=predTrainSigWeight,label="Train sig", alpha=0.6)
plt.hist(predTestBkg, bins=40, range=[0,1], histtype='step', color='cornflowerblue', linewidth=2, linestyle='--', weights=predTestBkgWeight,label="Test bkg")
plt.hist(predTestSig, bins=40, range=[0,1], histtype='step', color='gold', linewidth=2, linestyle='--', weights=predTestSigWeight,label="Test sig")
plt.xlim([0.0,1.0])
plt.xlabel("Score")
plt.ylabel("Normalized events")
plt.tight_layout(rect=[0., 0, 1, 0.91])
plt.legend(ncol=2, bbox_to_anchor=(0, 1.0), loc="lower left")
plt.savefig(outputName+"_dist.pdf")
plt.close()


