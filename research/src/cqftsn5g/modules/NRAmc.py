import math
from enum import Enum
import logging
from cqftsn5g.modules.NRMcs import (
    N_INFO_TO_TBS,
    TBSTABLESIZE,
    NRMcsTable,
    CQIelem,
    NRMCSelem,
    LteMod,
)

from cqftsn5g.modules.UserTxParams import UserTxParams


class Direction(Enum):
    DL = 0
    UL = 1
    D2D = 2
    D2D_MULTI = 3
    UNKNOWN_DIRECTION = 4


def get_mcs_elem_per_cqi(cqi: int, dir: Direction) -> NRMCSelem:
    # if dir == Direction.DL:
    #     mcs_table = mcs_table.dl_nr_mcs_table
    # elif dir in [Direction.UL, Direction.D2D, Direction.D2D_MULTI]:
    #     mcs_table = mcs_table.ul_nr_mcs_table
    # else:
    #     raise ValueError("Unrecognized direction")
    mcs_table = NRMcsTable()

    logging.debug(f"search for CQI: {cqi}")
    entry: CQIelem = mcs_table.get_cqi_elem(cqi)
    mod = entry.mod
    rate = entry.rate
    logging.debug(f"mod: {mod}, rate: {rate}")
    min_index = mcs_table.get_min_index(mod)
    max_index = mcs_table.get_max_index(mod)
    logging.debug(f"min_index: {min_index}, max_index: {max_index}")
    ret = mcs_table.at(min_index)
    for i in range(min_index, max_index + 1):
        elem: NRMCSelem = mcs_table.at(i)
        if elem.coderate <= rate:
            logging.debug(f"found MCS elem: {i}, coderate: {elem.coderate}")
            ret = elem
        else:
            break

    return ret


class SlotFormat:
    def __init__(self, tdd: bool, numDlSymbols: int, numUlSymbols: int, numFlexSymbols: int):
        self.tdd = tdd
        self.numDlSymbols = numDlSymbols
        self.numUlSymbols = numUlSymbols
        self.numFlexSymbols = numFlexSymbols


class BandLimit:
    def __init__(self, band: int, limit: list[int]):
        self.band = band
        self.limit = limit


class CarrierInfo:
    def __init__(
        self,
        carrierFrequency: float,
        numBands: int,
        firstBand: int,
        lastBand: int,
        bandLimit: list[BandLimit],
        numerologyIndex: int,
        slotFormat: SlotFormat,
    ):
        self.carrierFrequency = carrierFrequency
        self.numBands = numBands
        self.firstBand = firstBand
        self.lastBand = lastBand
        self.bandLimit = bandLimit
        self.numerologyIndex = numerologyIndex
        self.slotFormat = slotFormat

    def get_slot_format(self) -> SlotFormat:
        return self.slotFormat


def get_symbols_per_slot(dir: Direction, sf: SlotFormat):
    totSymbols = 14
    if not sf.tdd:
        return totSymbols

    if dir == Direction.DL:
        return sf.numDlSymbols
    else:
        return sf.numUlSymbols


def compute_codeword_tbs(info: UserTxParams, cw: int, dir: Direction, numRe: int):
    """
    Computes the codeword Transport Block Size (TBS) based on the given UserTxParams, codeword index, direction, and number of resource elements.

    Parameters:
    info (UserTxParams): The user transmission parameters.
    cw (int): The codeword index.
    dir (Direction): The transmission direction.
    numRe (int): The number of resource elements.

    Returns:
    int: The computed codeword TBS.
    """
    layers = info.get_layers()
    mcsElem = get_mcs_elem_per_cqi(info.read_cqi_vector()[cw], dir)

    match mcsElem.mod:
        case LteMod._QPSK:
            modFactor = 2
        case LteMod._16QAM:
            modFactor = 4
        case LteMod._64QAM:
            modFactor = 6
        case LteMod._256QAM:
            modFactor = 8
        case _:
            raise ValueError("Unrecognized modulation")

    coderate = mcsElem.coderate / 1024
    nInfo = numRe * coderate * modFactor * layers[cw]
    logging.debug(f"number of resource elements: {numRe}")
    logging.debug(f"coderate: {coderate}")
    logging.debug(f"modFactor: {modFactor}")
    logging.debug(f"layers len: {layers[cw]}")
    logging.debug(f"calculated nInfo: {nInfo}")
    return compute_tbs_from_ninfo(math.floor(nInfo), coderate)


def compute_tbs_from_ninfo(nInfo, coderate) -> int:
    """
    Computes the Transport Block Size (TBS) based on the given information and coderate.

    Parameters:
    nInfo (int): The information value used to compute the TBS.
    coderate (float): The coderate value used to compute the TBS.

    Returns:
    int: The computed Transport Block Size.
    """
    tbs = 0
    _nInfo = 0
    n = 0

    if nInfo == 0:
        return 0
    if nInfo <= 3824:
        n = max(3, math.floor(math.log2(nInfo) - 6))
        _nInfo = max(24, math.floor((1 << n) * math.floor(nInfo / (1 << n))))

        # get tbs from table
        tbs = next(
            (N_INFO_TO_TBS[j] for j in range(TBSTABLESIZE - 1) if N_INFO_TO_TBS[j] >= _nInfo),
            0,
        )
        # j = 0
        # for j in range(0, TBSTABLESIZE - 1):
        #     if N_INFO_TO_TBS[j] >= _nInfo:
        #         break
        # tbs = N_INFO_TO_TBS[j]
    else:
        n = math.floor(math.log2(nInfo - 24) - 5)
        _nInfo = (1 << n) * round((nInfo - 24) / (1 << n))
        if coderate <= 0.25:
            C = math.ceil((_nInfo + 24) / 3816)
            tbs = 8 * C * math.ceil((_nInfo + 24) / (8 * C)) - 24
        else:
            if _nInfo >= 8424:
                C = math.ceil((_nInfo + 24) / 8424)
                tbs = 8 * C * math.ceil((_nInfo + 24) / (8 * C)) - 24
            else:
                tbs = 8 * math.ceil((_nInfo + 24) / 8) - 24

    return tbs


def get_resource_elements_per_block(symbolsPerSlot):
    numSubcarriers = 12
    reSignal = 1
    nOverhead = 0
    if symbolsPerSlot == 0:
        return 0
    return (numSubcarriers * symbolsPerSlot) - reSignal - nOverhead


def get_resource_elements(blocks, symbolsPerSlot):
    numRePerBlock = get_resource_elements_per_block(symbolsPerSlot)

    if numRePerBlock > 156:
        return 156 * blocks

    return blocks * symbolsPerSlot


def compute_req_rbs(
    id,
    band,
    cw,
    bytes,
    dir,
    info: UserTxParams,
    carrierInfo: CarrierInfo,
):
    logging.info(f"NRAmc::computeReqRbs Node: {id}, Band: {band}, Codeword: {cw}, direction: {dir}")

    if bytes == 0:
        logging.debug("NRAmc::computeReqRbs Occupation: 0 bytes")
        logging.debug("NRAmc::computeReqRbs Number of RBs: 0")
        return 0

    # info = computeTxParams(id, dir, carrierFrequency);

    bits = bytes * 8
    sf: SlotFormat = carrierInfo.get_slot_format()
    numRe = get_resource_elements(1, get_symbols_per_slot(dir, sf))
    j = 0
    while j < 110:
        if compute_codeword_tbs(info, cw, dir, numRe) >= bits:
            break
        j += 1

    logging.debug(
        f"NRAmc::computeReqRbs Occupation: {bytes} bytes, CQI: {info.read_cqi_vector().at(cw)}"
    )
    logging.debug(f"NRAmc::computeReqRbs Number of RBs: {j + 1}")

    return j + 1


def compute_bits_on_n_rbs(
    id: int,
    band: int,
    blocks: int,
    dir: Direction,
    info: UserTxParams,
    carrierInfo: CarrierInfo,
):
    if blocks == 0:
        return 0

    logging.debug(f"NRAmc::computeBitsOnNRbs Node: {id}")
    logging.debug(f"NRAmc::computeBitsOnNRbs Band: {band}")
    logging.debug(f"NRAmc::computeBitsOnNRbs Direction: {dir}")

    sf: SlotFormat = carrierInfo.get_slot_format()
    numRe = get_resource_elements(blocks, get_symbols_per_slot(dir, sf))

    bits = 0
    codewords = len(info.get_layers())
    for cw in range(codewords):
        if info.read_cqi_vector()[cw] == 0:
            logging.debug(
                f"NRAmc::computeBitsOnNRbs - CQI equal to zero on cw {cw}, return no blocks available"
            )
        tbs = compute_codeword_tbs(info, cw, dir, numRe)
        bits += tbs

    logging.debug(f"NRAmc::computeBitsOnNRbs Resource Blocks: {blocks}")
    logging.debug(f"NRAmc::computeBitsOnNRbs Available space: {bits}")
    return bits
