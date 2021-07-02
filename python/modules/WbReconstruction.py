import os
import sys
import ROOT
import random

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module



class WbReconstruction(Module):
    RANDOM      = 1 # select random W boson
    TOP_BIAS    = 2 # select W boson with Wb closer to top mass
    LOW_MET_PZ  = 3 # select W boson with lower pz MET value
    HIGH_PT     = 4 # select highest PT

    def __init__(self,
                 WbosonCollection = 'Reco_w',
                 bjetCollection = 'BJet',
                 outputName = 'Reco_wb',
                 WbosonSelection = TOP_BIAS,
                 BSelection = HIGH_PT,
                 top_mass = 172.5,
                 offshell_mass_window = 20,
                 ):
        self.bjetCollection = bjetCollection
        self.WbosonCollection = WbosonCollection
        self.outputName = outputName
        self.WbosonSelection = WbosonSelection
        self.BSelection = BSelection
        self.top_mass = top_mass
        self.offshell_mass_window = offshell_mass_window


    def beginJob(self):
        pass


    def endJob(self):
        pass


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch(self.outputName + '_W_idx', 'I')
        self.out.branch(self.outputName + '_b_idx', 'I')

        self.out.branch(self.outputName + '_pt', 'F')
        self.out.branch(self.outputName + '_eta', 'F')
        self.out.branch(self.outputName + '_phi', 'F')
        self.out.branch(self.outputName + '_mass', 'F')

        self.out.branch(self.outputName + '_onshell', 'I')
        self.out.branch(self.outputName + '_chargeCorrelation', 'I')



    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def analyze(self, event):
        wbosons = self.WbosonCollection(event)
        bjets = self.bjetCollection(event)

        W_idx, b_idx = -99, -99


        if len(wbosons) == 1:
            W_idx = 0

        elif self.WbosonSelection == WbReconstruction.RANDOM:
            W_idx = random.randrange(0, len(wbosons))

        elif self.WbosonSelection == WbReconstruction.LOW_MET_PZ:
            met0, met1 = ROOT.TLorentzVector(), ROOT.TLorentzVector()
            met0.SetPtEtaPhiM(wbosons[0].met_pt, wbosons[0].met_eta, wbosons[0].met_phi, 0)
            met1.SetPtEtaPhiM(wbosons[1].met_pt, wbosons[1].met_eta, wbosons[1].met_phi, 0)

            if abs(met0.Pz()) < abs(met1.Pz()):
                W_idx = 0
            else:
                W_idx = 1

        elif self.WbosonSelection != WbReconstruction.TOP_BIAS:
            raise Exception('unknown WbosonSelection in WbReconstruction module')




        if len(bjets) == 1:
            b_idx = 0

        elif self.BSelection == WbReconstruction.RANDOM:
            b_idx = random.randrange(0, len(bjets))

        elif self.BSelection == WbReconstruction.HIGH_PT:
            b_idx = -1

            for i, jet in enumerate(bjets):
                if bjets[i].pt > bjets[b_idx].pt:
                    b_idx = i

        elif self.BSelection != WbReconstruction.TOP_BIAS:
            raise Exception('unknown BSelection in WbReconstruction module')



        # Top TOP_BIAS
        if self.WbosonSelection == WbReconstruction.TOP_BIAS or self.BSelection == WbReconstruction.TOP_BIAS:
            W_cand, b_cand = None, None

            if self.WbosonSelection == WbReconstruction.TOP_BIAS:
                W_cand = range(len(wbosons))
            else:
                W_cand = [W_idx]

            if self.BSelection == WbReconstruction.TOP_BIAS:
                b_cand = range(len(bjets))
            else:
                b_cand = [b_idx]

            best_top_mass_diff = 99999
            for W_cand_idx in W_cand:
                for b_cand_idx in b_cand:
                    massdiff = abs((wbosons[W_cand_idx].p4() + bjets[b_cand_idx].p4()).M() - self.top_mass)

                    if massdiff < best_top_mass_diff:
                        best_top_mass_diff = massdiff
                        W_idx = W_cand_idx
                        b_idx = b_cand_idx



        self.out.fillBranch(self.outputName + '_W_idx', W_idx)
        self.out.fillBranch(self.outputName + '_b_idx', b_idx)

        if W_idx >=0 and b_idx>=0:
            Wb = wbosons[W_idx].p4() + bjets[b_idx].p4()
            self.out.fillBranch(self.outputName + '_pt', Wb.Pt())
            self.out.fillBranch(self.outputName + '_eta', Wb.Eta())
            self.out.fillBranch(self.outputName + '_phi', Wb.Phi())
            self.out.fillBranch(self.outputName + '_mass', Wb.M())

            self.out.fillBranch(self.outputName + '_onshell', 1 if abs(Wb.M() - self.top_mass) < self.offshell_mass_window else 0)

            chargecorr = wbosons[W_idx].charge * bjets[b_idx].charge
            if chargecorr > 0:
                self.out.fillBranch(self.outputName + '_chargeCorrelation', 1)
            elif chargecorr < 0:
                self.out.fillBranch(self.outputName + '_chargeCorrelation', -1)
            else:
                self.out.fillBranch(self.outputName + '_chargeCorrelation', 0)

        return True
