#include <omnetpp.h>

#include <iostream>

#include "NRAmcpub.h"

using namespace omnetpp;
using namespace inet;
using namespace std;

int main() {
    std::cout << "Starting Simu5G Standalone Program" << std::endl;

    double carrierFrequency = 2.6e9;  // 2.6 GHz
    Direction dir = DL;

    // declare CQI = 13
    Cqi cqi = 13;

    // call getMcsElemPerCqi with cqi
    NRMCSelem mcsElem = NRAmcpub::getMcsElemPerCqi(cqi, dir);

    // printout mcsElem
    std::cout << "Modulation: " << mcsElem.mod_ << std::endl;
    std::cout << "Rate: " << mcsElem.coderate_ << std::endl;
    std::cout << "CQI: " << cqi << std::endl;

    // // Calculate the required number of resource blocks (RBs) for a given MAC node ID, band, codeword, number of bytes, direction, and carrier frequency
    // MacNodeId id = 1;           // MAC node ID
    // Band b = 0;                 // Band
    // unsigned int bytes = 1000;  // Number of bytes
    // Codeword cw = 0;
    // unsigned int reqRbs = amc->computeReqRbs(id, b, cw, bytes, dir, carrierFrequency);

    // // Calculate the number of bits that can be transmitted on a given number of RBs for a given MAC node ID, band, number of blocks, direction, and carrier frequency
    // unsigned int blocks = 10;  // Number of blocks
    // unsigned int bitsOnRbs = amc->computeBitsOnNRbs(id, b, blocks, dir, carrierFrequency);

    // // Calculate the number of bits that can be transmitted per RB in the background for a given CQI, direction, and carrier frequency
    // unsigned int bitsPerRb = amc->computeBitsPerRbBackground(cqi, dir, carrierFrequency);

    return 0;
}
