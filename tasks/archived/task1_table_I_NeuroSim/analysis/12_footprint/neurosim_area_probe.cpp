// Area-chain diagnostic only. No area in this probe populates the ten-case table.
#include <iomanip>
#include <iostream>
#include "Param.h"
#include "ProcessingUnit.h"
Param *param = nullptr;
static void emit(const char *key, double v) { std::cout << key << "=" << std::setprecision(17) << v << "\n"; }
int main() {
    param = new Param();
    // Main-owned fields are explicit; constructor primaries are patched before compilation.
    param->synapseBit = 1; param->numBitInput = 1;
    param->numColPerSynapse = 1; param->numRowPerSynapse = 1;
    param->numColMuxed = 1; param->levelOutput = 2; param->dumcolshared = 2;
    param->clkFreq = 1e8; param->synchronous = false;
    param->novelMapping = false; param->pipeline = false;
    InputParameter input{}; Technology tech; MemCell cell{}; SubArray *array = nullptr;
    ProcessingUnitInitialize(array, input, tech, cell, 1, 1, 1, 1);
    emit("memcelltype", param->memcelltype); emit("rows", array->numRow); emit("columns", array->numCol);
    emit("tech_featureSize_m", tech.featureSize); emit("cell_featureSize_m", cell.featureSize);
    emit("param_featuresize_m", param->featuresize); emit("cell_width_in_feature_size", cell.widthInFeatureSize);
    emit("cell_height_in_feature_size", cell.heightInFeatureSize);
    emit("relaxArrayCellWidth", array->relaxArrayCellWidth); emit("relaxArrayCellHeight", array->relaxArrayCellHeight);
    emit("lengthRow_m", array->lengthRow); emit("lengthCol_m", array->lengthCol);
    emit("areaArray_m2", array->areaArray); emit("usedArea_m2", array->usedArea);
    emit("area_m2", array->area); emit("emptyArea_m2", array->emptyArea);
    emit("areaArray_um2", array->areaArray*1e12);
    emit("array_bit_area_um2", array->areaArray*1e12/(array->numRow*array->numCol));
    emit("param_arrayheight_m", param->arrayheight); emit("param_arraywidthunit_m", param->arraywidthunit);
    return 0;
}
