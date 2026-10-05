#include <iomanip>
#include <iostream>
#include <random>
#include "Cell.h"
std::mt19937 gen(0);
int main() {
    DigitalNVM c(0,0);
    const double i0=c.Read(0.5);
    c.Write(1, 2e-15);
    const double i1=c.Read(0.5), e1=c.writeEnergy;
    c.Write(1, 2e-15);
    const double unchangedEnergy=c.writeEnergy;
    c.Write(0, 2e-15);
    std::cout << std::setprecision(17)
      << "{\"read0_A\":" << i0 << ",\"read1_A\":" << i1
      << ",\"set_energy_J\":" << e1 << ",\"unchanged_energy_field_J\":" << unchangedEnergy
      << ",\"reset_energy_J\":" << c.writeEnergy
      << ",\"write_pulse_LTP_s\":" << c.writePulseWidthLTP
      << ",\"write_pulse_LTD_s\":" << c.writePulseWidthLTD
      << ",\"resistance_access_ohm\":" << c.resistanceAccess
      << ",\"read0_after_reset_A\":" << c.Read(0.5) << "}" << std::endl;
}
