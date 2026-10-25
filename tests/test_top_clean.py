#!/usr/bin/env python3
"""Ensure live TOP pixels are not overwritten by debug rasterization."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
s=(root/'source/wipi_shim.cpp').read_text()
main=(root/'source/main.cpp').read_text()
head=(root/'source/wipi_shim.h').read_text()
assert 'mspe_diag_render' not in s
assert 'probe_rect' not in s and 'probe_text' not in s
assert 'kProbeAlphabet' not in s
assert 'mspe_diag_render' not in main
assert 'void wipi_boot_stage(const char *stage)' in s
boot=s.split('void wipi_boot_stage(const char *stage) {',1)[1].split('\n}\n',1)[0]
assert 'runner_ui_log_push_line(stage);' in boot
assert 'g_ds_fb' not in boot and 'REG_VRAM' not in boot and 'probe_' not in boot
mark=s.split('static void mspe_diag_mark(const char *phase) {',1)[1].split('\n}\n',1)[0]
assert 'g_ui_dirty=true;' in mark and 'g_ds_fb' not in mark
present=s.split('void wipi_present(void) {',1)[1].split('\n}\n',1)[0]
assert 'copy_phone_rect_to_ds_buf(g_sub_comp,0,0,PHONE_W,HALF_H,DST_X,TOP_DST_Y)' in present
assert 'dmaCopy(g_sub_comp,g_ds_fb,LCD_BYTES);' in present
assert 'mspe_diag' not in present
assert 'mspe_diag_render' not in s
assert 'boot/progress text' in main
assert 'optional SUB LOG' in head
# The exception is framebuffer setup/normal guest output, never debug instrumentation.
assert not re.search(r'probe_rect\(|probe_text\(',s)
print('PASS: TOP screen is exclusive to game pixels, diagnostics remain on SUB LOG.')
