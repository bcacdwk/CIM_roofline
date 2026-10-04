| 案例 | 逻辑 K×N | 原生模块入口（非案例闭合） | 混合/候选阶段 | 保留原生完整服务 |
|---|---:|---|---|---|
| 01_sram_acim | 128×128 | input_capture, sar, output_commit | reconstruct | charge_front, sram_write |
| 02_sram_dcim | 128×16 | input_capture, output_commit |  | native_mac, sram_write |
| 03_nor_2d | 128×128 | input_capture, operand_capture, output_commit | digital_mac, page_load, sector_erase | binary_read, page_program |
| 04_nand_3d | 4608×240 | input_capture, sar, output_commit | input_magnitude_sign, affine_merge_sign〔原算术预算〕, resident_encode, page_load, load_calibration〔原算术预算〕 | native_wl, native_bl_sl, page_program, block_erase |
| 05_rram | 128×64 | input_capture, sar, output_commit, attempt_done | digital_reconstruct, program_attempts, resident_front | analog_front, rail_setup, endpoint_verify, rail_exit |
| 06_mram | 256×32 | input_capture, operand_capture, output_commit, polarity_turn | digital_mac, encoded_load, terminal_verify | binary_read, direction_write |
| 07_pcm | 256×128 | input_capture, sar, output_commit | digital_reconstruct, resident_front, program_reset_set, endpoint_verify | analog_front |
| 08_feram_hfo2 | 128×128 | input_capture, output_commit | digital_mac, external_load | binary_read, external_polarization_write |
| 09_gain_cell_edram | 64×64 | input_capture, sar, output_commit | digital_reconstruct, resident_load, refresh_read, refresh_decode_load_rewrite | analog_front, current_program |
| 10_fenor_3d | 128×128 | input_capture, operand_capture, output_commit | digital_mac, resident_load, terminal_verify | binary_read, two_phase_write, post_pulse_guard |
