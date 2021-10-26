from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

class GenWeightProducer(Module):
    def __init__(self, isSignal=False):
        self.isSignal = isSignal

        self.nPDFs = 103
        self.nPSweights = 4
        self.nMEweights = 9

        if self.isSignal:
            self.nPDFs = 101

        # to be added once new files available
        self.fragWeights = []
        # self.fragWeights = ['fragCP5BLVsPt','fragCP5BLdownVsPt','fragCP5BLupVsPt',
        #                     'fragCP5PetersonVsPt','fragCP5PetersondownVsPt','fragCP5PetersonupVsPt',
        #                     'semilepbrdown','semilepbrup']

        pass

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        # PDF weights
        for PDF in range(0,self.nPDFs):
            self.out.branch('PDFweight_{}'.format(PDF),'F')

        # ME weights
        if self.nMEweights > 0:
            self.out.branch('MEweight_murDown_mufDown','F')
            self.out.branch('MEweight_murDown_mufNominal','F')
            self.out.branch('MEweight_murDown_mufUp','F')
            self.out.branch('MEweight_murNominal_mufDown','F')
            self.out.branch('MEweight_murNominal_mufNominal','F')
            self.out.branch('MEweight_murNominal_mufUp','F')
            self.out.branch('MEweight_murUp_mufDown','F')
            self.out.branch('MEweight_murUp_mufNominal','F')
            self.out.branch('MEweight_murUp_mufUp','F')

        # PS weights
        if self.nPSweights > 0:
            self.out.branch('PSweight_ISRUp_FSRNominal','F')
            self.out.branch('PSweight_ISRNominal_FSRUp','F')
            self.out.branch('PSweight_ISRDown_FSRNominal','F')
            self.out.branch('PSweight_ISRNominal_FSRDown','F')

        for fragWeight in self.fragWeights:
            self.out.branch('fragEventWeight_{}'.format(fragWeight),'F')


    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        
        if self.nPDFs > 0 and event.nLHEPdfWeight != self.nPDFs:
            raise ValueError('wrong number of PDF eigenvectors')
        if self.nMEweights > 0 and event.nLHEScaleWeight != self.nMEweights:
            raise ValueError('wrong number of ME weights')
        if self.nPSweights > 0 and event.nPSWeight != self.nPSweights:
            raise ValueError('wrong number of PS weights')
          
        for i in range(0,self.nPDFs):
            self.out.fillBranch('PDFweight_{}'.format(i), event.LHEPdfWeight[i])

        # MEweights = getattr(event,'LHEScaleWeight')
        if self.nMEweights > 0:
            self.out.fillBranch('MEweight_murDown_mufDown',event.LHEScaleWeight[0])
            self.out.fillBranch('MEweight_murDown_mufNominal',event.LHEScaleWeight[1])
            self.out.fillBranch('MEweight_murDown_mufUp',event.LHEScaleWeight[2])
            self.out.fillBranch('MEweight_murNominal_mufDown',event.LHEScaleWeight[3])
            self.out.fillBranch('MEweight_murNominal_mufNominal',event.LHEScaleWeight[4])
            self.out.fillBranch('MEweight_murNominal_mufUp',event.LHEScaleWeight[5])
            self.out.fillBranch('MEweight_murUp_mufDown',event.LHEScaleWeight[6])
            self.out.fillBranch('MEweight_murUp_mufNominal',event.LHEScaleWeight[7])
            self.out.fillBranch('MEweight_murUp_mufUp',event.LHEScaleWeight[8])

        # PSweights = getattr(event,'PSWeight')
        if self.nPSweights > 0:
            self.out.fillBranch('PSweight_ISRUp_FSRNominal',event.PSWeight[0])
            self.out.fillBranch('PSweight_ISRNominal_FSRUp',event.PSWeight[1])
            self.out.fillBranch('PSweight_ISRDown_FSRNominal',event.PSWeight[2])
            self.out.fillBranch('PSweight_ISRNominal_FSRDown',event.PSWeight[3])

        for fragWeight in self.fragWeights:
            weight = 1.
            for i in range(0,len(getattr(event,'GenJet_{}'.format(fragWeight)))):
                weight *= getattr(event,'GenJet_{}'.format(fragWeight)).At(i)
            self.out.fillBranch('fragEventWeight_{}'.format(fragWeight),weight)

        return True


