#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <cstdlib>
#include <new>
using namespace std;
#include "Param.h"
#include "typedef.h"
#ifdef PROBE_CAP
#include "ProcessingUnit.h"
#include "SubArray.h"
#endif

Param *param;
int main(int argc, char **argv) {
    // Zero storage makes fields not assigned by the upstream constructor explicit.
    alignas(Param) unsigned char storage[sizeof(Param)] = {};
    param = new (storage) Param();
    cout << setprecision(17);
#ifdef PROBE_CAP
    if (argc != 3) return 2;
    param->numRowParallel = atoi(argv[1]);
    param->chargeDelay = atof(argv[2]);
    param->synapseBit = 1;
    param->numBitInput = 1;
    param->numColPerSynapse = 1;
    param->numRowPerSynapse = 1;
    param->novelMapping = false;
    InputParameter input{};
    Technology tech;
    MemCell cell{};
    SubArray *sub = nullptr;
    ProcessingUnitInitialize(sub, input, tech, cell, 1, 1, 1, 1);
    sub->activityRowRead = 1;
    vector<double> columns(param->numColSubArray, 1e20);
    sub->CalculateLatency(1e20, columns, true);
    cout << "{\"symbol\":\"v15::Cap\",\"config_memcelltype\":" << param->memcelltype
         << ",\"enum_value\":" << int(Type::Cap)
         << ",\"node_nm\":" << param->technode
         << ",\"active_rows\":" << sub->numRowParallel
         << ",\"charge_delay_input_s\":" << param->chargeDelay
         << ",\"col_delay_raw_s\":" << sub->colDelay
         << ",\"sensing_critical_raw_s\":" << sub->readLatency
         << ",\"area_m2\":" << sub->area
         << ",\"beta\":" << param->beta
         << ",\"cell_on_ohm\":" << cell.resistanceOn
         << ",\"constructor_access_ohm\":" << param->resistanceAccess
         << "}" << endl;
#else
    cout << "{\"symbol\":\"dcim_v10::DCIM\",\"config_memcelltype\":" << param->memcelltype
         << ",\"enum_value\":" << int(Type::DCIM)
         << ",\"rows\":" << param->numRowSubArray
         << ",\"columns\":" << param->numColSubArray
         << ",\"parallel_weightprecision\":" << param->parallel_weightprecision
         << ",\"node_nm\":" << param->technode << "}" << endl;
#endif
    return 0;
}
