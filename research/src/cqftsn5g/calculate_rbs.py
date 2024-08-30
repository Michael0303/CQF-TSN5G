import logging
import math

from cqftsn5g.modules.UserTxParams import TxMode
from modules.UserTxParams import UserTxParams
from modules.NRAmc import CarrierInfo, Direction, compute_bits_on_n_rbs


def req_n_rbs(
    id: int,
    dir: Direction,
    userTxParams: UserTxParams,
    payload: int,
    blocksPerBand: int,
    carrierInfo: CarrierInfo,
) -> int:
    bandCount = 0
    toServed = payload
    while toServed > 0:
        # Calculate the bits can be transmiited on each band
        bits = compute_bits_on_n_rbs(id, bandCount, blocksPerBand, dir, userTxParams, carrierInfo)
        logging.info(f"band {bandCount} can trasmit {bits} bits = {bits / 8} bytes")

        toServed -= bits / 8
        bandCount += 1
    logging.info(f"total allocation bytes = {payload - toServed}")
    return bandCount


def req_rbs(
    CQI: int,
    carrierInfo: CarrierInfo,
    payload: int,
    id: int = 0,
    dir: Direction = Direction.DL,
    blocksPerBand: int = 1,
) -> int:
    userTxParams = UserTxParams(txMode=TxMode.TRANSMIT_DIVERSITY, ri=1, cqiVector=[CQI], pmi=0)
    selectedCQI = userTxParams.read_cqi_vector()[0]
    bits = compute_bits_on_n_rbs(id, 0, blocksPerBand, dir, userTxParams, carrierInfo)
    logging.info(f"band in CQI {selectedCQI} can trasmit {bits} bits = {bits / 8} bytes")

    return math.ceil(payload / (bits / 8))
