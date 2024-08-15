from enum import Enum


class TxMode(Enum):
    SINGLE_ANTENNA_PORT0 = 0
    SINGLE_ANTENNA_PORT5 = 1
    TRANSMIT_DIVERSITY = 2
    OL_SPATIAL_MULTIPLEXING = 3
    CL_SPATIAL_MULTIPLEXING = 4
    MULTI_USER = 5
    UNKNOWN_TX_MODE = 6


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
    def __init__(self, txMode: TxMode, ri: int, cqiVector: list[int], pmi: int):
        self.txMode = txMode
        self.ri = ri
        self.cqiVector: list[int] = cqiVector
        self.pmi = pmi
        self.allowedBands = []
        self.isValid = set()
        self.antennaSet = set()

    def get_layers(self) -> list[int]:
        antennaPorts = self.ri
        res = []
        if self.ri <= 1:
            res.append(1)
        else:
            match self.txMode:
                case (
                    TxMode.SINGLE_ANTENNA_PORT0
                    | TxMode.SINGLE_ANTENNA_PORT5
                    | TxMode.MULTI_USER
                ):
                    res.append(1)

                case TxMode.TRANSMIT_DIVERSITY:
                    res.append(antennaPorts)

                case TxMode.OL_SPATIAL_MULTIPLEXING | TxMode.CL_SPATIAL_MULTIPLEXING:
                    usedRi = antennaPorts if antennaPorts < self.ri else self.ri
                    if usedRi == 2:
                        res.append(1)
                        res.append(1)
                    elif usedRi == 3:
                        res.append(1)
                        res.append(2)
                    elif usedRi == 4:
                        res.append(2)
                        res.append(2)
                    elif usedRi == 8:
                        res.append(4)
                        res.append(4)
                case _:
                    res.append(1)
        return self.layers

    def read_cqi_vector(self) -> list[int]:
        return self.cqiVector
