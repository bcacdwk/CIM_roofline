#include <cmath>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>
#include "Param.h"
#include "ProcessingUnit.h"
#include "Definition.h"

// Static storage makes otherwise uninitialized upstream scalar members zero.
// Each invocation is a fresh process and initializes this one supported probeArray.
static SubArray probeArray(inputParameter, tech, cell);

static void setup(int parallelism) {
    const double step = std::ldexp(1.0, -20);
    param->memcelltype = 2;
    param->minConductance = step;
    param->maxConductance = 9 * step;
    param->resistanceOn = 1 / param->maxConductance;
    param->resistanceOff = 1 / param->minConductance;
    param->maxNumLevelLTP = param->maxNumLevelLTD = 8;
    param->cellBit = 3;
    param->numBitInput = param->synapseBit = 1;
    param->numColPerSynapse = param->numRowPerSynapse = 1;
    param->numRowSubArray = param->numColSubArray = 128;
    param->numColMuxed = 1;
    param->SARADC = true;
    param->trainingEstimation = false;
    inputParameter.temperature = param->temp;
    inputParameter.processNode = param->technode;
    inputParameter.transistorType = conventional;
    inputParameter.deviceRoadmap = LSTP;
    tech.Initialize(inputParameter.processNode, LSTP, conventional);
    cell.memCellType = Type::RRAM;
    cell.accessType = CMOS_access;
    cell.resistanceOn = param->resistanceOn;
    cell.resistanceOff = param->resistanceOff;
    cell.resistanceAvg = (cell.resistanceOn + cell.resistanceOff) / 2;
    cell.readVoltage = param->readVoltage;
    cell.readPulseWidth = param->readPulseWidth;
    cell.accessVoltage = param->accessVoltage;
    cell.resistanceAccess = param->resistanceAccess;
    cell.featureSize = param->featuresize;
    cell.maxNumLevelLTP = cell.maxNumLevelLTD = 8;
    cell.writeVoltage = std::sqrt(2.0) * param->writeVoltage;
    cell.writePulseWidth = param->writePulseWidth;
    cell.nonlinearIV = false;
    cell.nonlinearity = param->nonlinearity;
    cell.heightInFeatureSize = param->heightInFeatureSize1T1R;
    cell.widthInFeatureSize = param->widthInFeatureSize1T1R;
    probeArray.trainingEstimation = false;
    probeArray.conventionalParallel = true;
    probeArray.conventionalSequential = false;
    probeArray.parallelBP = false;
    probeArray.currentMode = true;
    probeArray.levelOutput = 16;
    probeArray.levelOutputBP = 16;
    probeArray.numColMuxed = probeArray.numRowMuxedBP = 1;
    probeArray.clkFreq = param->clkFreq;
    probeArray.numReadPulse = probeArray.numReadPulseBP = 1;
    probeArray.avgWeightBit = 3;
    probeArray.numCellPerSynapse = 1;
    probeArray.SARADC = true;
    probeArray.spikingMode = NONSPIKING;
    probeArray.activityRowRead = 1;
    probeArray.activityColWrite = 0.5;
    probeArray.activityRowWrite = 0.5;
    probeArray.numReadCellPerOperationFPGA = probeArray.numReadCellPerOperationMemory = probeArray.numReadCellPerOperationNeuro = 128;
    probeArray.numWriteCellPerOperationFPGA = probeArray.numWriteCellPerOperationMemory = 128;
    probeArray.numWriteCellPerOperationNeuro = parallelism;
    probeArray.maxNumWritePulse = 8;
    probeArray.numWritePulseAVG = 1;
    probeArray.totalNumWritePulse = 1;
    probeArray.Initialize(128, 128, param->unitLengthWireResistance);
    probeArray.CalculateArea();
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    const std::string name = argv[1];
    const int parallelism = std::stoi(argv[2]);
    setup(parallelism);
    const double step = std::ldexp(1.0, -20);
    std::vector<std::vector<double>> oldMemory(2, std::vector<double>(4, 4 * step));
    auto newMemory = oldMemory;
    if (name == "set") newMemory[0] = {6*step,5*step,4*step,4*step};
    else if (name == "reset") newMemory[0] = {2*step,3*step,4*step,4*step};
    else if (name == "mixed") newMemory[0] = {6*step,1*step,4*step,4*step};
    else if (name == "two_set_rows") {newMemory[0] = {6*step,5*step,4*step,4*step};newMemory[1][0]=5*step;}
    else if (name == "all_set") newMemory.assign(2, std::vector<double>(4, 6*step));
    else if (name != "unchanged") return 3;
    double ac=0, ar=0, energy=0;
    int avg=0, total=0;
    GetWriteUpdateEstimation(&probeArray, tech, cell, newMemory, oldMemory, &ac, &ar, &avg, &total, &energy);
    // The estimator probe is 2 x 4. For the separate scheduling probe, the
    // same aggregate activity fractions apply to the default-size 128 x 128 probeArray.
    probeArray.activityColWrite = ac;
    probeArray.activityRowWrite = ar;
    probeArray.numWritePulseAVG = avg;
    probeArray.totalNumWritePulse = total;
    probeArray.CalculateLatency(1e20, std::vector<double>(128, 100000.0), std::vector<double>(128, 100000.0));
    std::cout << std::setprecision(17)
      << "{\"case\":\"" << name << "\",\"parallelism\":" << parallelism
      << ",\"estimator_rows\":2,\"estimator_cols\":4,\"latency_probe_rows\":128,\"latency_probe_cols\":128"
      << ",\"min_delta_S\":" << step << ",\"activity_col\":" << ac << ",\"activity_row\":" << ar
      << ",\"pulse_average\":" << avg << ",\"pulse_total\":" << total
      << ",\"cell_pulse_s\":" << cell.writePulseWidth << ",\"write_latency_array_s\":" << probeArray.writeLatencyArray
      << ",\"write_latency_total_s\":" << probeArray.writeLatency << ",\"write_energy_estimator_J\":" << energy
      << ",\"technode_nm\":" << param->technode << ",\"clock_Hz\":" << probeArray.clkFreq
      << ",\"cap_row1_F\":" << probeArray.capRow1 << ",\"cap_row2_F\":" << probeArray.capRow2 << ",\"cap_col_F\":" << probeArray.capCol
      << "}" << std::endl;
}
