import math
from enum import Enum

class LteMod(Enum):
    _QPSK = 0
    _16QAM = 1
    _64QAM = 2
    _256QAM = 3


class NRMCSelem:
    def __init__(self, mod = LteMod._QPSK, coderate = 0.0):
        self.mod = mod # modulation (Qm)
        self.coderate = coderate # code rate (R)


class NRMcsTable:
    def __init__(self, extended=True):
        self.extended = extended
        self.cqi_table = []  # list of CQIelem
        self.table = []  # list of NRMCSelem

    def get_cqi_elem(self, cqi):
        return self.cqi_table[cqi]

    def get_min_index(self, mod):
        # implementation depends on the actual logic
        pass

    def get_max_index(self, mod):
        # implementation depends on the actual logic
        pass

    def at(self, tbs):
        return self.table[tbs]

def get_mcs_elem_per_cqi(cqi, dir, mcs_table):
    """
    Returns the NRMCSelem corresponding to the given CQI value and direction.

    :param cqi: CQI value (int)
    :param dir: direction (DL, UL, D2D, etc.)
    :param mcs_table: NRMcsTable instance
    :return: NRMCSelem instance
    """
    if dir == 'DL':
        mcs_table = mcs_table.dl_nr_mcs_table
    elif dir in ['UL', 'D2D', 'D2D_MULTI']:
        mcs_table = mcs_table.ul_nr_mcs_table
    else:
        raise ValueError("Unrecognized direction")

    cqi_elem = mcs_table.get_cqi_elem(cqi)
    mod = cqi_elem.mod
    min_index = mcs_table.get_min_index(mod)
    max_index = mcs_table.get_max_index(mod)

    for i in range(min_index, max_index + 1):
        elem = mcs_table.at(i)
        if elem.coderate <= cqi_elem.rate:
            return elem
        else:
            break

    return None