import logging
from modules.NRAmc import CarrierInfo, Direction, SlotFormat
from modules.UserTxParams import TxMode, UserTxParams
from calculate_rbs import req_rbs


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    slotFormat = SlotFormat(
        tdd=True,
        numDlSymbols=6,
        numUlSymbols=6,
        numFlexSymbols=2,
    )

    sf_fdd = SlotFormat(
        tdd=False,
        numDlSymbols=6,
        numUlSymbols=6,
        numFlexSymbols=2,
    )

    carrierInfo = CarrierInfo(
        carrierFrequency=5.9,
        numBands=50,
        firstBand=0,
        lastBand=49,
        bandLimit=[],
        numerologyIndex=2,
        slotFormat=sf_fdd,
    )

    chosenCQI = 9
    ue = UserTxParams(txMode=TxMode.TRANSMIT_DIVERSITY, ri=1, cqiVector=[chosenCQI], pmi=0)
    payload = 662
    n = req_rbs(333, Direction.DL, ue, payload, 1, carrierInfo)
    print(f"need {n} resource blocks to transmit payload {payload} (bytes)")
