import os
import sys
import math
import ROOT
import scipy.optimize

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module



class WbosonReconstruction(Module):
    def __init__(self,
                 electronCollectionName = 'Electron',
                 muonCollectionName = 'Muon',
                 metName = 'MET',
                 outputName='Reco_W',
                 Wmass = 80.385,
                 debug=False
                 ):
        self.electronCollectionName = electronCollectionName
        self.muonCollectionName = muonCollectionName
        self.metName = metName
        self.outputName=outputName
        self.Wmass = Wmass

        self.debug = debug


    def beginJob(self):
        pass


    def endJob(self):
        pass


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        self.out.branch(self.outputName + '_pt', 'F')
        self.out.branch(self.outputName + '_eta', 'F')
        self.out.branch(self.outputName + '_phi', 'F')
        self.out.branch(self.outputName + '_mass', 'F')

        self.out.branch(self.metName + '_etaFromW', 'F')


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass


    def analyze(self, event):
        electrons = Collection(event, self.electronCollectionName)
        muons = Collection(event, self.muonCollectionName)
        metObj = Object(event, self.metName)

        met = ROOT.TLorentzVector()
        met.SetPtEtaPhiM(metObj.pt, 0, metObj.phi, 0)


        lep = None
        if len(electrons)==1 and len(muons)==0:
            lep = electrons[0].p4()
        elif len(electrons)==0 and len(muons)==1:
            lep = muons[0].p4()
        else:
            print('Error: Found multiple leptons! No W reconstruction possible.')
            return False


        recoMet = self.recoMetFromWmass(lep, met)
        W = lep + recoMet



        self.out.fillBranch(self.outputName + '_pt', W.Pt())
        self.out.fillBranch(self.outputName + '_eta', W.Eta())
        self.out.fillBranch(self.outputName + '_phi', W.Phi())
        self.out.fillBranch(self.outputName + '_mass', W.M())

        self.out.fillBranch(self.metName + '_etaFromW', recoMet.Eta())

        return True


    def recoMetFromWmass(self, lep, nu):
        '''
        aka the real thorsten method
        '''

        # definition of the constant mu in Eq. 4.5 (here called alpha to not confuse mu and nu)
        # also converting p_T and cos dphi into p_x and p_y
        alpha = (self.Wmass**2 / 2) + (lep.Px() * nu.Px()) + (lep.Py() * nu.Py())

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
                return self.Wmass**2 + 4 * lep.Px() * x

            # the delta plus function with the p_y^nu plus solution
            def min_f1(x):
                r = rad_py(x)
                y = (self.Wmass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * x + self.Wmass * lep.Pt() * math.sqrt(r)) / (2 * lep.Px()**2)
                res = math.sqrt((x - pxmiss)**2 + (y - pymiss)**2)
                #print('... x: %f, f(x): %f, rad: %f' %(x,res,r))
                return res

            # the delta minus function with the p_y^nu minus solution
            def min_f2(x):
                r = rad_py(x)
                y = (self.Wmass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * x - self.Wmass * lep.Pt() * math.sqrt(r)) / (2 * lep.Px()**2)
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
            x_bound = -((self.Wmass**2) / (4 * lep.Px()))

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
                pynew = (self.Wmass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * pxnew + self.Wmass * lep.Pt() * math.sqrt(rad_py(pxnew))) / (2 * lep.Px()**2)
            else:
                best_fit = 2
                pxnew = fit2.x[0]
                pynew = (self.Wmass**2 * lep.Py() + 2 * lep.Px() * lep.Py() * pxnew - self.Wmass * lep.Pt() * math.sqrt(rad_py(pxnew))) / (2 * lep.Px()**2)

            # calculate remaining single p_z solution with fixed p_x and p_y
            pznew = lep.Pz() / lep.Pt()**2 * ((self.Wmass**2 / 2) + (lep.Px() * pxnew) + (lep.Py() * pynew))

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
            return nu


        else:
            # for real solutions:
            #print('REAL p_z')
            # calculate both solutions
            sol1 = lep.Pz() * alpha / lep.Pt()**2 + math.sqrt(rad)
            sol2 = lep.Pz() * alpha / lep.Pt()**2 - math.sqrt(rad)

            # choose the smaller one
            if abs(sol1) < abs(sol2):
                nu.SetPz(sol1)
            else:
                nu.SetPz(sol2)

            nu.SetE(nu.P())

            #print('re: %f' %((lep + nu).Eta()))
            return nu

