from enum import Enum


class LteMod(Enum):
    _QPSK = 0
    _16QAM = 1
    _64QAM = 2
    _256QAM = 3


class CQIelem:
    def __init__(self, mod=LteMod._QPSK, rate=0.0):
        self.mod = mod
        self.rate = rate


class MCSelem:
    def __init__(self, mod=LteMod._QPSK, iTbs=0, threshold=0.0):
        self.mod = mod
        self.iTbs = iTbs
        self.threshold = threshold


class NRMCSelem:
    def __init__(self, mod=LteMod._QPSK, coderate=0.0):
        self.mod = mod
        self.coderate = coderate


TBSTABLESIZE = 94

N_INFO_TO_TBS = [
    0,
    24,
    32,
    40,
    48,
    56,
    64,
    72,
    80,
    88,
    96,
    104,
    112,
    120,
    128,
    136,
    144,
    152,
    160,
    168,
    176,
    184,
    192,
    208,
    224,
    240,
    256,
    272,
    288,
    304,
    320,
    336,
    352,
    368,
    384,
    408,
    432,
    456,
    480,
    504,
    528,
    552,
    576,
    608,
    640,
    672,
    704,
    736,
    768,
    808,
    848,
    888,
    928,
    984,
    1032,
    1064,
    1128,
    1160,
    1192,
    1224,
    1256,
    1288,
    1320,
    1352,
    1416,
    1480,
    1544,
    1608,
    1672,
    1736,
    1800,
    1864,
    1928,
    2024,
    2088,
    2152,
    2216,
    2280,
    2408,
    2472,
    2536,
    2600,
    2664,
    2728,
    2792,
    2856,
    2976,
    3104,
    3240,
    3368,
    3496,
    3624,
    3752,
    3824,
]


class NRMcsTable:
    def __init__(self, extended=True):
        self.extended = extended
        self.cqiTable = []
        self.mcsTable = []
        if not self.extended:
            self.cqiTable = [
                CQIelem(LteMod._QPSK, 0.0),
                CQIelem(LteMod._QPSK, 78.0),
                CQIelem(LteMod._QPSK, 120.0),
                CQIelem(LteMod._QPSK, 193.0),
                CQIelem(LteMod._QPSK, 308.0),
                CQIelem(LteMod._QPSK, 449.0),
                CQIelem(LteMod._QPSK, 602.0),
                CQIelem(LteMod._16QAM, 378.0),
                CQIelem(LteMod._16QAM, 490.0),
                CQIelem(LteMod._16QAM, 616.0),
                CQIelem(LteMod._64QAM, 466.0),
                CQIelem(LteMod._64QAM, 567.0),
                CQIelem(LteMod._64QAM, 666.0),
                CQIelem(LteMod._64QAM, 772.0),
                CQIelem(LteMod._64QAM, 873.0),
                CQIelem(LteMod._64QAM, 948.0),
            ]
            self.mcsTable = [
                NRMCSelem(LteMod._QPSK, 120.0),
                NRMCSelem(LteMod._QPSK, 157.0),
                NRMCSelem(LteMod._QPSK, 193.0),
                NRMCSelem(LteMod._QPSK, 251.0),
                NRMCSelem(LteMod._QPSK, 308.0),
                NRMCSelem(LteMod._QPSK, 379.0),
                NRMCSelem(LteMod._QPSK, 449.0),
                NRMCSelem(LteMod._QPSK, 526.0),
                NRMCSelem(LteMod._QPSK, 602.0),
                NRMCSelem(LteMod._QPSK, 679.0),
                NRMCSelem(LteMod._16QAM, 340.0),
                NRMCSelem(LteMod._16QAM, 378.0),
                NRMCSelem(LteMod._16QAM, 434.0),
                NRMCSelem(LteMod._16QAM, 490.0),
                NRMCSelem(LteMod._16QAM, 553.0),
                NRMCSelem(LteMod._16QAM, 616.0),
                NRMCSelem(LteMod._16QAM, 658.0),
                NRMCSelem(LteMod._64QAM, 438.0),
                NRMCSelem(LteMod._64QAM, 466.0),
                NRMCSelem(LteMod._64QAM, 517.0),
                NRMCSelem(LteMod._64QAM, 567.0),
                NRMCSelem(LteMod._64QAM, 616.0),
                NRMCSelem(LteMod._64QAM, 666.0),
                NRMCSelem(LteMod._64QAM, 719.0),
                NRMCSelem(LteMod._64QAM, 772.0),
                NRMCSelem(LteMod._64QAM, 822.0),
                NRMCSelem(LteMod._64QAM, 873.0),
                NRMCSelem(LteMod._64QAM, 910.0),
                NRMCSelem(LteMod._64QAM, 948.0),
            ]
        else:
            self.cqiTable = [
                CQIelem(LteMod._QPSK, 0.0),
                CQIelem(LteMod._QPSK, 78.0),
                CQIelem(LteMod._QPSK, 193.0),
                CQIelem(LteMod._QPSK, 449.0),
                CQIelem(LteMod._16QAM, 378.0),
                CQIelem(LteMod._16QAM, 490.0),
                CQIelem(LteMod._16QAM, 616.0),
                CQIelem(LteMod._64QAM, 466.0),
                CQIelem(LteMod._64QAM, 567.0),
                CQIelem(LteMod._64QAM, 666.0),
                CQIelem(LteMod._64QAM, 772.0),
                CQIelem(LteMod._64QAM, 873.0),
                CQIelem(LteMod._256QAM, 711.0),
                CQIelem(LteMod._256QAM, 797.0),
                CQIelem(LteMod._256QAM, 885.0),
                CQIelem(LteMod._256QAM, 948.0),
            ]
            self.mcsTable = [
                NRMCSelem(LteMod._QPSK, 120.0),
                NRMCSelem(LteMod._QPSK, 193.0),
                NRMCSelem(LteMod._QPSK, 308.0),
                NRMCSelem(LteMod._QPSK, 449.0),
                NRMCSelem(LteMod._QPSK, 602.0),
                NRMCSelem(LteMod._16QAM, 378.0),
                NRMCSelem(LteMod._16QAM, 434.0),
                NRMCSelem(LteMod._16QAM, 490.0),
                NRMCSelem(LteMod._16QAM, 553.0),
                NRMCSelem(LteMod._16QAM, 616.0),
                NRMCSelem(LteMod._16QAM, 658.0),
                NRMCSelem(LteMod._64QAM, 466.0),
                NRMCSelem(LteMod._64QAM, 517.0),
                NRMCSelem(LteMod._64QAM, 567.0),
                NRMCSelem(LteMod._64QAM, 616.0),
                NRMCSelem(LteMod._64QAM, 666.0),
                NRMCSelem(LteMod._64QAM, 719.0),
                NRMCSelem(LteMod._64QAM, 772.0),
                NRMCSelem(LteMod._64QAM, 822.0),
                NRMCSelem(LteMod._64QAM, 873.0),
                NRMCSelem(LteMod._256QAM, 682.5),
                NRMCSelem(LteMod._256QAM, 711.0),
                NRMCSelem(LteMod._256QAM, 754.0),
                NRMCSelem(LteMod._256QAM, 797.0),
                NRMCSelem(LteMod._256QAM, 841.0),
                NRMCSelem(LteMod._256QAM, 885.0),
                NRMCSelem(LteMod._256QAM, 916.5),
                NRMCSelem(LteMod._256QAM, 948.0),
            ]

    def get_cqi_elem(self, i):
        # print(f"CQI table index: {i}")
        return self.cqiTable[i]

    def get_min_index(self, mod):
        if not self.extended:
            if mod == LteMod._QPSK:
                return 0
            elif mod == LteMod._16QAM:
                return 10
            elif mod == LteMod._64QAM:
                return 17
            else:
                raise ValueError("Modulation not supported")
        else:
            if mod == LteMod._QPSK:
                return 0
            elif mod == LteMod._16QAM:
                return 5
            elif mod == LteMod._64QAM:
                return 11
            elif mod == LteMod._256QAM:
                return 20
            else:
                raise ValueError("Modulation not supported")

    def get_max_index(self, mod):
        if not self.extended:
            if mod == LteMod._QPSK:
                return 9
            elif mod == LteMod._16QAM:
                return 16
            elif mod == LteMod._64QAM:
                return 28
            else:
                raise ValueError("Modulation not supported")
        else:
            if mod == LteMod._QPSK:
                return 4
            elif mod == LteMod._16QAM:
                return 10
            elif mod == LteMod._64QAM:
                return 19
            elif mod == LteMod._256QAM:
                return 27
            else:
                raise ValueError("Modulation not supported")

    def at(self, tbs):
        return self.mcsTable[tbs]
