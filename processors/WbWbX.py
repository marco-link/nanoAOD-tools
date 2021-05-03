import argparse

from PhysicsTools.NanoAODTools.modules import *
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor


parser = argparse.ArgumentParser()

parser.add_argument('--isData', dest='isData', action='store_true', default=False)
parser.add_argument('--isSignal', dest='isSignal', action='store_true', default=False)
parser.add_argument('--nofilter', action='store_true', default=False, help='do not apply branch filters to the output')
parser.add_argument('--year', dest='year', action='store', type=int, default=2016)
parser.add_argument('--input', dest='inputFiles', action='append', default=[])
parser.add_argument('--maxEntries', '-N', type=int, default=None)
parser.add_argument('output', nargs=1)



args = parser.parse_args()
print(args)

year = args.year
isSignal = args.isSignal
isData = args.isData
isMC = not isData


Wboson_mass = 80.385
top_mass = 172.5
offshell_mass_window = 20


triggers = {
            2016: '(HLT_IsoMu24 == 1) || (HLT_IsoTkMu24 == 1) || (HLT_Ele32_eta2p1_WPTight_Gsf==1)',
            2017: '(HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned == 1) || (HLT_Ele35_WPTight_Gsf == 1) || (HLT_IsoMu27==1)',
            2018: '(HLT_IsoMu24 == 1) || (HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned == 1) || (HLT_Ele32_WPTight_Gsf == 1)'
          }[year] if not isSignal else ''

minMuonPt = {2016: 25., 2017: 28., 2018: 25.}[year]
minElectronPt = {2016: 29., 2017: 34., 2018: 34.}[year]

met_object = {
    2016: lambda event: Object(event, "MET"),
    2017: lambda event: Object(event, "METFixEE2017"),
    2018: lambda event: Object(event, "MET")
}[year]



# TODO verify/use up to date WPs
looseWP = {
            2016: 0.06140,
            2017: 0.05210,
            2018: 0.04940
          }[year]

mediumWP = {
            2016: 0.30930,
            2017: 0.30330,
            2018: 0.27700
           }[year]

tightWP = {
            2016: 0.72210,
            2017: 0.74890,
            2018: 0.72640
          }[year]



analyzerChain = [

    WbGenProducer(dRmax=0.4) if isSignal and not isData else DummyModule(),

    # particle selections/filters
    MetFilter(
        isData = isData,
        outputName = 'MET_filter'
    ),
    EventSkim(selection = lambda event: event.MET_filter == 1),

    ########
    # Muon #
    ########
    MuonSelection(
        inputCollection=lambda event: Collection(event, 'Muon'),
        outputName='tightMuons',
        storeKinematics=['mass', 'pt', 'eta', 'phi', 'charge'],
        storeWeights=True,
        muonMinPt=minMuonPt,
        triggerMatch=True,
        muonID=MuonSelection.TIGHT,
        muonIso=MuonSelection.VERYTIGHT,
        year=year,
        isData=isData,
    ),

    #SingleMuonTriggerSelection(
        #inputCollection=lambda event: event.tightMuon,
        #outputName="IsoMuTrigger",
        #storeWeights=True,
        #year=year,
        #isData=isData,
    #),
    #EventSkim(selection=lambda event: event.IsoMuTrigger_flag > 0),


    ############
    # Electron #
    ############

    # TODO Electron selection + trigger


    #TODO What happens here? Also Electrons?
    ###EventSkim(selection=lambda event: event.IsoMuTrigger_flag > 0),
    ###MuonVeto(
        ###inputCollection=lambda event: event.tightMuons_unselected,
        ###outputName = "vetoMuons",
        ###muonMinPt = 10.,
        ###muonMaxEta = 2.4,
        ###globalOptions=globalOptions
    ###),
    ###EventSkim(selection=lambda event: event.nvetoMuons == 0),




    EventSkim(selection = lambda event: event.ntightMuons==1 or event.nElectron==1),


    ########
    # Jets #
    ########

    JetSelection(
        inputCollection=lambda event: Collection(event, 'Jet'),
        leptonCollectionDRCleaning=lambda event: Collection(event, 'tightMuons') if event.ntightMuons==1 else Collection(event, 'Electron'),
        jetMinPt=30.,
        jetMaxEta=4.7,
        jetId=JetSelection.LOOSE,
        outputName='nominal_selectedJets',
        storeKinematics=['mass',  'pt','eta', 'phi', 'partonFlavour', 'btagDeepFlavB'],
    ),

    # TODO BTagging SF
    BTagSelection(
        inputCollection=lambda event: event.nominal_selectedJets,
        outputBName="nominal_selectedBJets",
        outputLName="nominal_selectedNonBJets",
        jetMinPt=30.,
        jetMaxEta=2.4,
        storeKinematics=['mass', 'pt', 'eta', 'phi', 'partonFlavour', 'btagDeepFlavB'],
        taggerFct=lambda obj: obj.btagDeepFlavB>tightWP and obj.pt>30 and obj.eta < 2.4,
    ),

    EventSkim(selection = lambda event: event.nnominal_selectedBJets    == 1 or (event.nnominal_selectedBJets    == 2 and event.nominal_selectedBJets[1].pt    < 50)),
    EventSkim(selection = lambda event: event.nnominal_selectedNonBJets == 1 or (event.nnominal_selectedNonBJets == 2 and event.nominal_selectedNonBJets[1].pt < 50)),
    EventSkim(selection = lambda event: abs(event.nominal_selectedNonBJets[0].eta) > 2.3),



    JetGenInfo(
        inputCollection=lambda event: event.nominal_selectedBJets,
        outputName='nominal_selectedBJets',
    ),

    JetGenChargeProducer(
        JetCollection=lambda event: event.nominal_selectedBJets,
        outputName='nominal_selectedBJets'
    ),

    ChargeTagging(
        modelPath = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/frozenModel.pb",
        featureDictFile = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/featureDict.py",
        inputCollections = [lambda event: event.nominal_selectedBJets],
        taggerName = "nominal_selectedBJets_Chargetagger",
    ),

    ##SimpleJetChargeSum(
        ##inputCollection=lambda event: event.nominal_selectedBJets,
        ##outputCollection="selectedBJets",
        ##outputName="betaChargeSum",
        ##beta=0.8,
        ##globalOptions=globalOptions
    ##),



    #TODO weights calculation


    ########
    # Reco #
    ########

    WbosonReconstruction(
        leptonObject = lambda event: Collection(event, 'tightMuons')[0] if event.ntightMuons==1 else Collection(event, 'Electron')[0],
        metObject = met_object,
        WbosonMass = Wboson_mass,
        outputName = 'Reco_W',
    ),

    WbReconstruction(
        WbosonCollection = lambda event: Collection(event, 'Reco_W'),
        bjetCollection = lambda event: Collection(event, 'nominal_selectedBJets'),
        outputName = 'Reco_Wb',
        WbosonSelection = WbReconstruction.LOW_MET_PZ,
        BSelection = WbReconstruction.HIGH_PT,
        top_mass = top_mass,
        offshell_mass_window = offshell_mass_window,
    ),

    EventSkim(selection=lambda event: event.Reco_W_mass[event.Reco_Wb_W_idx] < 120 and abs(event.Reco_W_eta[event.Reco_Wb_W_idx]) < 4.0 ),

    CalculateVariable(
        function = lambda event: (Collection(event, 'Reco_W')[event.Reco_Wb_W_idx].p4() + Collection(event, 'nominal_selectedNonBJets')[0].p4()).M() if len(Collection(event, 'nominal_selectedNonBJets')) > 0 else -99,
        outputName = 'Reco_WNonB_mass',
        vartype='F'
    ),
    EventSkim(selection=lambda event: event.Reco_WNonB_mass > 140),







    ## apply binning for asymmetry
    #AsymBinProducer(
        #massBranch='Reco_wb_mass',
        #chargeBranch='Reco_wb_bjet_charge',
        #outputName='Reco_AsymBin',
        #mass=top_mass,
        #masswindow=offshell_mass_window
    #),


    #if signal
    ## calculate asymmetry for generator truth
    #step3_analyzerChain.append(AsymBinProducer(
                                    #massBranch='Gen_wb_mass',
                                    #chargeBranch='Gen_wb_b_Charge',
                                    #outputName='Reco_GenAsymBin',
                                    #mass=top_mass,
                                    #masswindow=offshell_mass_window
                               #))
]



if not isData:
    storeVariables = [
    [lambda tree: tree.branch("PV_npvs", "I"), lambda tree,
     event: tree.fillBranch("PV_npvs", event.PV_npvs)],
    [lambda tree: tree.branch("PV_npvsGood", "I"), lambda tree,
     event: tree.fillBranch("PV_npvsGood", event.PV_npvsGood)],
    [lambda tree: tree.branch("fixedGridRhoFastjetAll", "F"), lambda tree,
     event: tree.fillBranch("fixedGridRhoFastjetAll",
                            event.fixedGridRhoFastjetAll)],
    ]

    storeVariables.append([lambda tree: tree.branch("genweight", "F"),
                           lambda tree,
                           event: tree.fillBranch("genweight",
                           event.Generator_weight)])

    if args.isSignal:
        for coupling in range(1,106):
            storeVariables.append([
                lambda tree, coupling=coupling: tree.branch('LHEWeights_width_%i'%coupling,'F'),
                lambda tree, event, coupling=coupling: tree.fillBranch('LHEWeights_width_%i'%coupling,getattr(event,"LHEWeights_width_%i"%coupling)),
            ])

    analyzerChain.append(EventInfo(storeVariables=storeVariables))


workflow = PostProcessor(
    args.output[0],
    args.inputFiles,
    postfix='_WbWbX',
    cut=triggers,
    modules=analyzerChain,
    friend=True,
    outputbranchsel=None if args.nofilter else 'processors/WbWbX_filter.txt',
    maxEntries=args.maxEntries,
)


# Run analysis
workflow.run()
