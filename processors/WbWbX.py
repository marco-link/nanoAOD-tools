import argparse

from PhysicsTools.NanoAODTools.modules import *
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor

#TODO use trigger selection
#triggers = {
            #2016: '(HLT_IsoMu24 == 1) || (HLT_IsoTkMu24 == 1) || (HLT_Ele32_eta2p1_WPTight_Gsf==1)',
            #2017: '(HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned == 1) || (HLT_Ele35_WPTight_Gsf == 1) || (HLT_IsoMu27==1)',
            #2018: '(HLT_IsoMu24 == 1) || (HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned == 1) || (HLT_Ele32_WPTight_Gsf == 1)'
        #}[year] if not isSignal else ''

def getAnalyzerChain(year, isSignal, isData):

    # constants
    Wboson_mass = 80.385
    top_mass = 172.5
    top_mass_window = 25

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




        EventSkim(selection = lambda event: event.ntightMuons == 1 or event.nElectron == 1),


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
            storeKinematics=['mass',  'pt', 'eta', 'phi', 'partonFlavour', 'btagDeepFlavB'],
        ),

        # TODO BTagging SF
        BTagSelection(
            inputCollection=lambda event: event.nominal_selectedJets,
            outputBName="nominal_selectedBJets",
            outputLName="nominal_selectedNonBJets",
            jetMinPt=30.,
            jetMaxEta=2.4,
            storeKinematics=['mass', 'pt', 'eta', 'phi', 'partonFlavour', 'btagDeepFlavB'],
            taggerFct = lambda obj: obj.btagDeepFlavB > tightWP and obj.pt > 30 and abs(obj.eta) < 2.4,
        ),

        EventSkim(selection = lambda event: event.nnominal_selectedBJets    == 1 or (event.nnominal_selectedBJets    == 2 and event.nominal_selectedBJets[1].pt    < 50)),
        EventSkim(selection = lambda event: event.nnominal_selectedNonBJets == 1 or (event.nnominal_selectedNonBJets == 2 and event.nominal_selectedNonBJets[1].pt < 50)),
        EventSkim(selection = lambda event: abs(event.nominal_selectedNonBJets[0].eta) > 2.3),



        JetGenInfo(
            inputCollection = lambda event: event.nominal_selectedBJets,
            outputName = 'nominal_selectedBJets',
        ),

        JetGenChargeProducer(
            JetCollection = lambda event: event.nominal_selectedBJets,
            outputName = 'nominal_selectedBJets'
        ),

        CalculateVariable(
            function = lambda event: map(lambda bjet: bjet.bPartonCharge, Collection(event, 'nominal_selectedBJets')),
            outputName = 'nominal_selectedBJets_charge',
            vartype = 'I',
            length = 'nnominal_selectedBJets'
        ),


        #ChargeTagging(
            #modelPath = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/frozenModel.pb",
            #featureDictFile = "${CMSSW_BASE}/src/PhysicsTools/NanoAODTools/data/nn/featureDict.py",
            #inputCollections = [lambda event: event.nominal_selectedBJets],
            #taggerName = "nominal_selectedBJets_Chargetagger",
        #),

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
            WbosonSelection = WbReconstruction.TOP_BIAS,
            BSelection = WbReconstruction.TOP_BIAS,
            top_mass = top_mass,
            offshell_mass_window = top_mass_window,
        ),

        #EventSkim(selection=lambda event: event.Reco_W_mass[event.Reco_Wb_W_idx] < 120 and abs(event.Reco_W_eta[event.Reco_Wb_W_idx]) < 4.0 ),

        #CalculateVariable(
            #function = lambda event: (Collection(event, 'Reco_W')[event.Reco_Wb_W_idx].p4() + Collection(event, 'nominal_selectedNonBJets')[0].p4()).M() if len(Collection(event, 'nominal_selectedNonBJets')) > 0 else -99,
            #outputName = 'Reco_WNonB_mass',
            #vartype='F'
        #),
        #EventSkim(selection=lambda event: event.Reco_WNonB_mass > 140),



    ]


    if isSignal and not isData:
        analyzerChain.append(PartonLevel())

        analyzerChain.append(
            WbReconstruction(
                WbosonCollection = lambda event: Collection(event, 'partonLevel_W'),
                bjetCollection = lambda event: Collection(event, 'partonLevel_bFromTop') if event.partonLevel_top_pt > 0 else Collection(event, 'partonLevel_bquarks'),
                outputName = 'partonLevel_Wb{}'.format(i),
                WbosonSelection = WbReconstruction.TOP_BIAS,
                BSelection = WbReconstruction.TOP_BIAS,
                top_mass = top_mass,
                offshell_mass_window = top_mass_window,
            )
        )


        analyzerChain.append(ParticleLevel())
        analyzerChain.append(
            WbosonReconstruction(
                leptonObject = lambda event: Object(event, 'particleLevel_lepton'),
                metObject = lambda event: Object(event, 'particleLevel_met'),
                WbosonMass = Wboson_mass,
                outputName = 'particleLevel_W',
            )
        )

        analyzerChain.append(
            WbReconstruction(
                WbosonCollection = lambda event: Collection(event, 'particleLevel_W'),
                bjetCollection = lambda event: Collection(event, 'particleLevel_bjets'),
                outputName = 'particleLevel_Wb{}'.format(i),
                WbosonSelection = WbReconstruction.TOP_BIAS,
                BSelection = WbReconstruction.TOP_BIAS,
                top_mass = top_mass,
                offshell_mass_window = top_mass_window,
            )
        )




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


    return analyzerChain



if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--isData', dest='isData', action='store_true', default=False)
    parser.add_argument('--isSignal', dest='isSignal', action='store_true', default=False)
    parser.add_argument('--crab', action='store_true', default=False, help='set if script is run by crab')
    parser.add_argument('--year', dest='year', action='store', type=int, default=2016)
    parser.add_argument('--input', dest='inputFiles', action='append', default=[])
    parser.add_argument('--maxEntries', '-N', type=int, default=None)
    parser.add_argument('--output', default='.',)



    args = parser.parse_args()
    print(args)


    moduleChain = getAnalyzerChain(args.year, args.isSignal, args.isData)


    p = None
    if args.crab:
        from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis

        p = PostProcessor(
            args.output,
            inputFiles(),
            cut="(nJet>1) && ((nElectron+nMuon)>0)",
            modules=moduleChain,
            friend=False,
            outputbranchsel='WbWbX_filter.txt',
            provenance=True,
            fwkJobReport=True,
            jsonInput=runsAndLumis()
        )
    else:
        p = PostProcessor(
            args.output,
            args.inputFiles,
            postfix='_WbWbX',
            cut="(nJet>1) && ((nElectron+nMuon)>0)",
            modules=moduleChain,
            friend=True,
            maxEntries=args.maxEntries,
        )


    # Run analysis
    p.run()
