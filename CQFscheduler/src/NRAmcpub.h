#include "stack/mac/amc/LteAmc.h"
#include "stack/mac/amc/NRAmc.h"
#include "stack/mac/amc/NRMcs.h"

class NRAmcpub : public NRAmc {
   public:
    static NRMCSelem getMcsElemPerCqi(Cqi cqi, const Direction dir);
};