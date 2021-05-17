from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from gen_helper import *



class WbGenProducer(Module):
    def __init__(self, dRmax, debug=False):
        self.debug = debug


        self.dRmax = dRmax

        self.genBranchName = "Gen_Wb"
        self.wBranchName = self.genBranchName + "_W_"
        self.bquarkBranchName = self.genBranchName + "_b_"
        self.wdauBranchName = self.genBranchName + "_Wdau_"

        self.genjetBranchName = "GenJet_Wb"
        self.bquarkjetBranchName = self.genjetBranchName + "_bjet_"
        self.nonmatchedjetBranchName = self.genjetBranchName + "_nonmatched"

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch(self.genBranchName + "_mass", "F")
        self.out.branch(self.genBranchName + "jet_mass", "F")

        self.out.branch(self.wBranchName + "pt", "F")
        self.out.branch(self.wBranchName + "eta", "F")
        self.out.branch(self.wBranchName + "phi", "F")
        self.out.branch(self.wBranchName + "mass", "F")

        self.out.branch(self.bquarkBranchName + "pt", "F")
        self.out.branch(self.bquarkBranchName + "eta", "F")
        self.out.branch(self.bquarkBranchName + "phi", "F")
        self.out.branch(self.bquarkBranchName + "pdgId", "I")
        self.out.branch(self.bquarkBranchName + "Charge", "F")

        self.out.branch(self.wdauBranchName + "pt", "F", 2)
        self.out.branch(self.wdauBranchName + "eta", "F", 2)
        self.out.branch(self.wdauBranchName + "phi", "F", 2)
        self.out.branch(self.wdauBranchName + "pdgId", "I", 2)

        self.out.branch(self.bquarkjetBranchName + "pt", "F")
        self.out.branch(self.bquarkjetBranchName + "eta", "F")
        self.out.branch(self.bquarkjetBranchName + "phi", "F")
        self.out.branch(self.bquarkjetBranchName + "mass", "F")

        self.out.branch(self.nonmatchedjetBranchName, "I")




    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        gen_particles = Collection(event, "GenPart")
        gen_jets = Collection(event, "GenJet")

        list_id = []

        idx = -1

        w = None
        w_idx = None

        bquark = None
        bquark_idx = None

        bquarkjet = None
        bquarkjet_idx = None

        j_idx = -1
        j_assigned = []

        wdau_pt = []
        wdau_eta = []
        wdau_phi = []
        wdau_m = []
        wdau_id = []
        wdau_idx = []




        if self.debug:
            ## debug block
            print "========================"
            print "====== new event ======="
            print "========================"
            jet_idx = -1
            print "--> gen jets"
            for j in gen_jets:
                jet_idx += 1
                print "%i \t\t %f \t %f \t %f \t %f \t %i \t %i " %(jet_idx,j.pt,j.eta,j.phi,j.mass,j.partonFlavour,j.hadronFlavour)
            idx = -1
            print "--> gen particles"
            for p in gen_particles:
                idx += 1
                print "%i \t %i \t %f \t %f \t %f \t %f \t %i \t %i %i %i %i %i %i %i %i %i %i %i %i %i %i %i " %(idx,p.genPartIdxMother,p.pt,p.eta,p.phi,p.mass,p.pdgId,int(isPrompt(p)),int(isDecayedLeptonHadron(p)),int(isTauDecayProduct(p)),int(isPromptTauDecayProduct(p)),int(isDirectTauDecayProduct(p)),int(isDirectPromptTauDecayProduct(p)),int(isDirectHadronDecayProduct(p)),int(isHardProcess(p)),int(fromHardProcess(p)),int(isHardProcessTauDecayProduct(p)),int(isDirectHardProcessTauDecayProduct(p)),int(fromHardProcessBeforeFSR(p)),int(isFirstCopy(p)),int(isLastCopy(p)),int(isLastCopyBeforeFSR(p)))
                if (idx > 20):
                    break



        idx = -1
        for p in gen_particles:

            # next gen particle, increase idx
            idx += 1


            # store id for each particle, so we can easily access the id of a particles mother
            list_id.append(p.pdgId)

            # skip initial partons
            if p.status == 21:
                continue

            # furthermore, skip also particles that appear out of nowhere
            if p.genPartIdxMother == -1:
                continue

            # W boson
            if (abs(p.pdgId) == 24) and fromHardProcess(p) and isLastCopy(p):
                w = p
                w_idx = idx

            # (bottom) quark
            if (abs(p.pdgId) == 5) and fromHardProcess(p) and isLastCopy(p):
                bquark = p
                bquark_idx = idx

            # W boson decay products
            if p.genPartIdxMother == w_idx:
                wdau_pt.append(p.pt)
                wdau_eta.append(p.eta)
                wdau_phi.append(p.phi)
                wdau_m.append(p.mass)
                wdau_id.append(p.pdgId)
                wdau_idx.append(idx)

        # end gen particle loop

        if w == None:
            print '### no W found!'
            w = genDummy()

        if bquark == None:
            print '### no bquark found!'
            bquark = genDummy()

        if len(wdau_id) != 2:
            print '### found %i wdau!' %len(wdau_id)

        check_idx = [w_idx, bquark_idx]
        for i in wdau_idx:
            check_idx.append(i)
        if len(set(check_idx)) != len(check_idx):
            print '### some gen particles have been assigned twice!'
            print check_idx
            print len(set(check_idx))
            print len(check_idx)


        for j in gen_jets:

            j_idx += 1

            if bquark.pdgId == j.partonFlavour:
                # print "bquarkjet parton flavor found"
                if j.p4().DeltaR(bquark.p4()) < self.dRmax:
                    # print "\t--> bquark gen jet found: %f" %(j.p4().DeltaR(bquark.p4()))
                    if j_idx not in j_assigned:
                        bquarkjet = j
                        bquarkjet_idx = j_idx
                        j_assigned.append(j_idx)

        nmatchedgenjets = len(j_assigned)
        nnonmatchedgenjets = len(gen_jets) - nmatchedgenjets

        if bquarkjet == None:
            bquarkjet = genDummy()



        self.out.fillBranch(self.wBranchName + "pt", w.pt)
        self.out.fillBranch(self.wBranchName + "eta", w.eta)
        self.out.fillBranch(self.wBranchName + "phi", w.phi)
        self.out.fillBranch(self.wBranchName + "mass", w.mass)

        self.out.fillBranch(self.bquarkBranchName + "pt", bquark.pt)
        self.out.fillBranch(self.bquarkBranchName + "eta", bquark.eta)
        self.out.fillBranch(self.bquarkBranchName + "phi", bquark.phi)
        self.out.fillBranch(self.bquarkBranchName + "pdgId", bquark.pdgId)
        self.out.fillBranch(self.bquarkBranchName + "Charge", getChargeFromPDG(bquark))

        # fill only if W boson was found
        if len(wdau_id) == 2:
            self.out.fillBranch(self.wdauBranchName + "pt", wdau_pt)
            self.out.fillBranch(self.wdauBranchName + "eta", wdau_eta)
            self.out.fillBranch(self.wdauBranchName + "phi", wdau_phi)
            self.out.fillBranch(self.wdauBranchName + "pdgId", wdau_id)


        self.out.fillBranch(self.bquarkjetBranchName + "pt", bquarkjet.pt)
        self.out.fillBranch(self.bquarkjetBranchName + "eta", bquarkjet.eta)
        self.out.fillBranch(self.bquarkjetBranchName + "phi", bquarkjet.phi)
        self.out.fillBranch(self.bquarkjetBranchName + "mass", bquarkjet.mass)

        self.out.fillBranch(self.nonmatchedjetBranchName, nnonmatchedgenjets)



        wb = w.p4() + bquark.p4()
        self.out.fillBranch(self.genBranchName + "_mass", wb.M())


        if bquarkjet.mass < 0:
            self.out.fillBranch(self.genBranchName + "jet_mass", bquarkjet.mass)
        else:
            wbjet = w.p4() + bquarkjet.p4()
            self.out.fillBranch(self.genBranchName + "jet_mass", wbjet.M())


        return True
