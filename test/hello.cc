#include <omnetpp.h>

#include <iostream>

#include "stack/mac/allocator/LteAllocationModule.h"
using namespace std;
int main() {
    cout << "hello world" << endl;
    unsigned int totalResourceBlocks = lteAllocationModule.computeTotalRbs();
    std::cout << "Total resource blocks: " << totalResourceBlocks << std::endl;
    return 0;
}