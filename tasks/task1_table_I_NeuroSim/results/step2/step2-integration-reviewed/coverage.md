| 案例 | 逻辑 K×N | NeuroSim 主调用 | 保留原生阶段 |
|---|---:|---|---|
| 01_sram_acim | 128×128 | input_capture, sar, reconstruct, output_commit | charge_front, sram_write |
| 02_sram_dcim | 128×16 | input_capture, output_commit | native_mac, sram_write |
| 03_nor_2d | 128×128 | input_capture, operand_capture, digital_mac, page_load, sector_erase, output_commit | binary_read, page_program |
| 04_nand_3d | 4608×240 | input_capture, input_magnitude_sign, sar, affine_merge_sign, resident_encode, page_load, load_calibration, output_commit | native_wl, native_bl_sl, page_program, block_erase |
| 05_rram | 128×64 | input_capture, sar, digital_reconstruct, program_attempts, endpoint_verify, output_commit, resident_front, attempt_done | analog_front, rail_setup, rail_exit |
| 06_mram | 256×32 | input_capture, operand_capture, digital_mac, encoded_load, terminal_verify, output_commit, polarity_turn | binary_read, direction_write |
| 07_pcm | 256×128 | input_capture, sar, digital_reconstruct, resident_front, program_reset_set, endpoint_verify, output_commit | analog_front |
| 08_feram_hfo2 | 128×128 | input_capture, digital_mac, external_load, output_commit | binary_read, external_polarization_write |
| 09_gain_cell_edram | 64×64 | input_capture, sar, digital_reconstruct, resident_load, refresh_read, refresh_decode_load_rewrite, output_commit | analog_front, current_program |
| 10_fenor_3d | 128×128 | input_capture, operand_capture, digital_mac, resident_load, terminal_verify, output_commit | binary_read, two_phase_write, post_pulse_guard |
