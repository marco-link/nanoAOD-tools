import os
import sys
import math
import ROOT
import scipy.optimize

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

from gen_helper import genDummy


class WbosonReconstruction(Module):
    def __init__(self,
        leptonObject = lambda event: Collection(event,"Muon")[0],
        metObject = lambda event: Object(event, "MET"),
        WbosonMass = 80.4,
        outputName='Reco_W',
        debug = False
    ):
        self.leptonObject = leptonObject
        self.metObject = metObject
        self.WbosonMass = WbosonMass
        self.outputName=outputName
        self.debug = debug

    def beginJob(self):
        pass


    def endJob(self):
        pass


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch('n' + self.outputName, 'I')
        self.out.branch(self.outputName + '_mass', 'F', lenVar="n"+self.outputName)
        self.out.branch(self.outputName + '_pt', 'F', lenVar="n"+self.outputName)
        self.out.branch(self.outputName + '_eta', 'F', lenVar="n"+self.outputName)
        self.out.branch(self.outputName + '_phi', 'F', lenVar="n"+self.outputName)
        self.out.branch(self.outputName + '_charge', 'I', lenVar="n"+self.outputName)

        self.out.branch(self.outputName + '_met_pt', 'F', lenVar="n"+self.outputName)
        self.out.branch(self.outputName + '_met_eta', 'F', lenVar="n"+self.outputName)
        self.out.branch(self.outputName + '_met_phi', 'F', lenVar="n"+self.outputName)

        self.out.branch(self.outputName + '_met_lepton_deltaR', 'F', lenVar="n"+self.outputName)
        self.out.branch(self.outputName + '_mtw', 'F', lenVar="n"+self.outputName)


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def analyze(self, event):
        lepton = self.leptonObject(event).p4()

        met = ROOT.TLorentzVector()
        met.SetPtEtaPhiM(self.metObject(event).pt, 0, self.metObject(event).phi, 0)

        nu_candidates, W_candidates = [], []

        # only reconstruct if lepton and met are valid
        if self.leptonObject(event).pt > 0 and met.Pt() > 0:
            nu_candidates = self.recoMetFromWmass(lepton, met)
            W_candidates = [lepton + nu for nu in nu_candidates]
        else:
            nu_candidates = [genDummy()]
            W_candidates = [genDummy()]
            print('no valid lepton/MET found for Wboson reconstruction')



        self.out.fillBranch('n' + self.outputName, len(nu_candidates))
        self.out.fillBranch(self.outputName + '_mass', map(lambda W: W.M(), W_candidates))
        self.out.fillBranch(self.outputName + '_pt', map(lambda W: W.Pt(), W_candidates))
        self.out.fillBranch(self.outputName + '_eta', map(lambda W: W.Eta(), W_candidates))
        self.out.fillBranch(self.outputName + '_phi', map(lambda W: W.Phi(), W_candidates))
        self.out.fillBranch(self.outputName + '_charge', map(lambda W: self.leptonObject(event).charge, W_candidates))

        self.out.fillBranch(self.outputName + '_met_pt', map(lambda met: met.Pt(), nu_candidates))
        self.out.fillBranch(self.outputName + '_met_eta', map(lambda met: met.Eta(), nu_candidates))
        self.out.fillBranch(self.outputName + '_met_phi', map(lambda met: met.Phi(), nu_candidates))

        self.out.fillBranch(self.outputName + '_met_lepton_deltaR', map(lambda met: met.DeltaR(lepton), nu_candidates))
        self.out.fillBranch(self.outputName + '_mtw', map(lambda met: math.sqrt( 2 * (1 - math.cos(met.DeltaPhi(lepton))) * lepton.Pt() * met.Pt()), nu_candidates))

        return True


    def recoMetFromWmass(self, lep, nu):
        '''
        aka the real thorsten method
        '''

        # definition of the constant mu in Eq. 4.5 (here called alpha to not confuse mu and nu)
        # also converting p_T and cos dphi into p_x and p_y
        alpha = (self.WbosonMass**2 / 2) + (lep.Px() * nu.Px()) + (lep.Py() * nu.Py())

        # for p_z,nu there is a quadratic equation with up to two solutions as shown in Eq. 4.6 and A.7
        # (NOTE: there is a 'power of two' missing in the first denominator of Eq. 4.6)
        # first, check if we have complex solution, i.e. if the radicand is negative
        rad = ((alpha**2 * lep.Pz()**2) / (lep.Pt()**4)) - ((lep.E()**2 * nu.Pt()**2 - alpha**2) / (lep.Pt()**2))

        if rad < 0:
            # complex solutions, should be around 30% of all cases:
            #print('COMPL p_z')
            # assumption: p_T^miss does not directly correspond to p_T,nu
            # set m_T^W to m^W, result is a quadratic equation for p_(x,y) that depends on p_(y,x)


            # save p_x^miss and p_y^miss as we need them later to determine the better solution
            pxmiss = nu.Px()
            pymiss = nu.Py()

            # search for both p_y solutions the corresponding p_x that minimizes the distance wrt p_x^miss and p_y^miss

            # helper function for minimizer constraint
            def rad_py(x):
                return self.WbosonMass**2 + 4 * lep.Px() * x

            # the delta plus function with the p_y^nu plus solution
            def min_f1(x):
                r = rad_py(x)
                y = (self.WbosonMass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * x + self.WbosonMass * lep.Pt() * math.sqrt(r)) / (2 * lep.Px()**2)
                res = math.sqrt((x - pxmiss)**2 + (y - pymiss)**2)
                #print('... x: %f, f(x): %f, rad: %f' %(x,res,r))
                return res

            # the delta minus function with the p_y^nu minus solution
            def min_f2(x):
                r = rad_py(x)
                y = (self.WbosonMass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * x - self.WbosonMass * lep.Pt() * math.sqrt(r)) / (2 * lep.Px()**2)
                res = math.sqrt((x - pxmiss)**2 + (y - pymiss)**2)
                #print('... x: %f, f(x): %f, rad: %f' %(x,res,r))
                return res

            # to make sure we start with a positive value for rad_py
            start_val = 0

            # restrict x solutions
            max_range = 9999
            min_range = -max_range
            bnds = [(min_range, max_range)]


            # try to implement constraints as bounds on fit parameter
            x_bound = -((self.WbosonMass**2) / (4 * lep.Px()))

            if x_bound > 0:
                max_range = x_bound - 1e-2
                start_val = max_range - 1
            elif x_bound < 0:
                min_range = x_bound + 1e-2
                start_val = min_range + 1
            else:
                sys.exit(1)

            bnds = [(min_range, max_range)]

            # run minimizer for delta plus
            fit1 = scipy.optimize.minimize(min_f1,
                                        start_val,
                                        #method = mthd,
                                        bounds = bnds)

            #print(fit1)

            # similar for delta minus
            fit2 = scipy.optimize.minimize(min_f2,
                                        start_val,
                                        #method = mthd,
                                        bounds = bnds)

            #print(fit2)

            # choose the one with smaller distance wrt p_x^miss and p_y^miss (aka delta)
            d1 = fit1.fun
            d2 = fit2.fun


            if d1 < d2:
                best_fit = 1
                pxnew = fit1.x[0]
                pynew = (self.WbosonMass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * pxnew + self.WbosonMass * lep.Pt() * math.sqrt(rad_py(pxnew))) / (2 * lep.Px()**2)
            else:
                best_fit = 2
                pxnew = fit2.x[0]
                pynew = (self.WbosonMass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * pxnew - self.WbosonMass * lep.Pt() * math.sqrt(rad_py(pxnew))) / (2 * lep.Px()**2)

            # calculate remaining single p_z solution with fixed p_x and p_y
            pznew = lep.Pz() / lep.Pt()**2 * ((self.WbosonMass**2 / 2) + (lep.Px() * pxnew) + (lep.Py() * pynew))

            # print('delta1: %f (%f), delta2: %f (%f)' %(fit1.fun, fit1.x[0], fit2.fun, fit2.x[0]))
            # print('x: %f, pxmiss: %f' %(pxnew, pxmiss))
            # print('y: %f, pymiss: %f' %(pynew, pymiss))
            # print('T: %f, pTmiss: %f' %(math.sqrt(pxnew**2+pynew**2), math.sqrt(pxmiss**2+pymiss**2)))

            nu.SetPxPyPzE(pxnew, pynew, pznew, math.sqrt(pxnew**2 + pynew**2 + pznew**2))


            if self.debug:
                print('fit1 result: d(x) = %f, x = %f, status %i, success %r' %(fit1.fun, fit1.x[0], fit1.status, fit1.success))
                print('fit2 result: d(x) = %f, x = %f, status %i, success %r' %(fit2.fun, fit2.x[0], fit2.status, fit2.success))
                print('choice: %i' %best_fit)

            #print('im: %f' %((lep + nu).Eta()))
            return [nu]


        else:
            # for real solutions:
            #print('REAL p_z')
            # calculate both solutions
            sol1 = lep.Pz() * alpha / lep.Pt()**2 + math.sqrt(rad)
            sol2 = lep.Pz() * alpha / lep.Pt()**2 - math.sqrt(rad)

            nu1, nu2 = ROOT.TLorentzVector(nu), ROOT.TLorentzVector(nu)
            nu1.SetPz(sol1)
            nu2.SetPz(sol2)

            nu1.SetE(nu1.P())
            nu2.SetE(nu2.P())

            #print('re: %f' %((lep + nu).Eta()))
            return [nu1, nu2]
