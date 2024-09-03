#include "NRAmcpub.h"

using namespace std;
using namespace omnetpp;

NRMCSelem NRAmcpub::getMcsElemPerCqi(Cqi cqi, const Direction dir) {
    // CQI threshold table selection
    // declare a mcsTable and a pointer to it
    NRMcsTable *mcsTable = new NRMcsTable(true);

    CQIelem entry = mcsTable->getCqiElem(cqi);
    LteMod mod = entry.mod_;
    double rate = entry.rate_;
    // printout mod and rate
    EV << "mod: " << mod << " rate: " << rate << endl;

    // Select the ranges for searching in the McsTable (extended reporting supported)
    unsigned int min = mcsTable->getMinIndex(mod);
    unsigned int max = mcsTable->getMaxIndex(mod);

    // Initialize the working variables at the minimum value.
    NRMCSelem ret = mcsTable->at(min);

    // Search in the McsTable from min to max until the rate exceeds
    // the coderate in an entry of the table.
    for (unsigned int i = min; i <= max; i++) {
        NRMCSelem elem = mcsTable->at(i);
        if (elem.coderate_ <= rate)
            ret = elem;
        else
            break;
    }
    delete mcsTable;
    // Return the MCSElem found.
    return ret;
}