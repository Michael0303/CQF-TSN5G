from enum import Enum

    
class PilotComputationModes(Enum):
    MIN_CQI = 0
    MAX_CQI = 1
    AVG_CQI = 2
    MEDIAN_CQI = 3
    ROBUST_CQI = 4
    
class Remote(Enum):
    MACRO = 0
    RU1 = 1
    RU2 = 2
    RU3 = 3
    RU4 = 4
    RU5 = 5
    RU6 = 6
    UNKNOWN_RU = 7
    
class UserTxParams:
    def __init__(self, txmode: TxMode, ri: int, cqiVector, pmi: int):
        self.txmode = txmode
        self.ri = ri
        self.cqiVector = cqiVector
        self.pmi = pmi
        self.allowedBands = []
        self.isValid = set()
        self.antennaSet = set()
    
    
    
    
class AmcPilotAuto:
    def __init__(self, amc, mode=PilotComputationModes.AVG_CQI):
        self.mode = mode
        self.amc = amc

    def compute_tx_params(self, id, dir, carrierFrequency):

        if self.amc.exist_tx_params(id, dir, carrierFrequency):
           return self.amc.get_tx_params(id, dir, carrierFrequency)

        txmode = TxMode.TRANSMIT_DIVERSITY

        sfb = self.amc.get_feedback(id, Remote.MACRO, txmode, dir, carrierFrequency)
        
        summaryCqi = sfb.get_cqi(0) 
        
        chosenCqi = 12
        
        if self.mode = PilotComputationModes.AVG_CQI:
            chosenCqi = getBinder().avgCqi(summaryCqi,id,dir)
        elif self.mode = PilotComputationModes.MEDIAN_CQI:
            chosenCqi = getBinder().medianCqi(summaryCqi,id,dir)
        elif self.mode = PilotComputationModes.ROBUST_CQI:
            chosenCqi = getBinder().medianCqi(summaryCqi,id,dir)

        info = UserTxParams(txmode, sfb.get_ri(), [chosenCqi], sfb.get_pmi(chosenBand), bandSet, set([Remote.MACRO]))

        userInfo = self.amc.set_tx_params(id, dir, info, carrierFrequency)
        
        return userInfo