
import numpy

def status_flag(p, n):
    '''
    To save space, the status flags for each gen particle are not stored as
    individual branches, instead they are encoded into a single integer branch
    called 'GenPart_statusFlags' and can be retrieved by reading single bits
    from that number

    Example: GenPart_statusFlags == 12 (decimal) == [0...]1100 (binary)
    -> flag 0 == False
    -> flag 1 == False
    -> flag 2 == True
    -> flag 3 == True
    -> flags >=4 == False

    The list of all flags and their bit index:

    0 : isPrompt
    1 : isDecayedLeptonHadron
    2 : isTauDecayProduct
    3 : isPromptTauDecayProduct
    4 : isDirectTauDecayProduct
    5 : isDirectPromptTauDecayProduct
    6 : isDirectHadronDecayProduct
    7 : isHardProcess
    8 : fromHardProcess
    9 : isHardProcessTauDecayProduct
    10 : isDirectHardProcessTauDecayProduct
    11 : fromHardProcessBeforeFSR
    12 : isFirstCopy
    13 : isLastCopy
    14 : isLastCopyBeforeFSR

    This functions takes as input a gen particle object and the index of the status
    flag, performs a bit shift of the status flag integer to move the corresponding
    bit to the right and returns whether the resulting number is odd (last bit == 1, True)
    or even (last bit == 0, False)
    '''
    return bool((p.statusFlags >> n) % 2 != 0)

def isPrompt(p):
    return status_flag(p, 0)

def isDecayedLeptonHadron(p):
    return status_flag(p, 1)

def isTauDecayProduct(p):
    return status_flag(p, 2)

def isPromptTauDecayProduct(p):
    return status_flag(p, 3)

def isDirectTauDecayProduct(p):
    return status_flag(p, 4)

def isDirectPromptTauDecayProduct(p):
    return status_flag(p, 5)

def isDirectHadronDecayProduct(p):
    return status_flag(p, 6)

def isHardProcess(p):
    return status_flag(p, 7)

def fromHardProcess(p):
    return status_flag(p, 8)

def isHardProcessTauDecayProduct(p):
    return status_flag(p, 9)

def isDirectHardProcessTauDecayProduct(p):
    return status_flag(p, 10)

def fromHardProcessBeforeFSR(p):
    return status_flag(p, 11)

def isFirstCopy(p):
    return status_flag(p, 12)

def isLastCopy(p):
    return status_flag(p, 13)

def isLastCopyBeforeFSR(p):
    return status_flag(p, 14)

def getMassFromPDG(p):
    if abs(p.pdgId) == 12 or abs(p.pdgId) == 14 or abs(p.pdgId) == 16:
        m = 0
    elif abs(p.pdgId) == 11:
        m = 0.00051
    elif abs(p.pdgId) == 13:
        m = 0.10566
    elif abs(p.pdgId) == 15:
        m = 1.77686
    elif abs(p.pdgId) == 5:
        m = 4.18
    else:
        m = -1
    return m


def getChargeFromPDG(p):
    charge = 0.

    if abs(p.pdgId) == 2 or abs(p.pdgId) == 4 or abs(p.pdgId) == 6: # up type quarks
        charge = numpy.sign(p.pdgId) * 0.666666
    elif abs(p.pdgId) == 1 or abs(p.pdgId) == 3 or abs(p.pdgId) == 5: # down type quarks
        charge = numpy.sign(p.pdgId) * -0.333333
    elif abs(p.pdgId) == 11 or abs(p.pdgId) == 13 or abs(p.pdgId) == 15: # charged leptons
        charge = -numpy.sign(p.pdgId)
    elif abs(p.pdgId) == 24: # W boson
        charge = numpy.sign(p.pdgId)

    return charge




# checks whether in the production chain of a particle (p) up to the incoming particles a particle with pdgId in ids exists
def motherchainContains(gen_particles, p, ids):
    mother = gen_particles[p.genPartIdxMother]
    while(mother.status != 21):
        if (mother.pdgId in ids):
            return True
        mother = gen_particles[mother.genPartIdxMother]
    return False


class genDummy:
    pt = -10
    eta = -10
    phi = -10
    mass = -10
    pdgId = 0

    def Pt(self):
        return self.pt

    def Eta(self):
        return self.eta

    def Phi(self):
        return self.phi

    def M(self):
        return self.mass

    def DeltaPhi(self, x):
        return 0

    def DeltaR(self, x):
        return -10
