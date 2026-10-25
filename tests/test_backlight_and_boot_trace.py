#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
s=(root/'source/wipi_shim.cpp').read_text()
assert re.search(r'case 0x578:\s*fn=\(void\*\)misc_backlight;',s)
assert re.search(r'extern "C" int misc_backlight\(uint32_t id,uint32_t on_off,uint32_t color,uint32_t timeout\)',s)
assert 'g_diag_last_unknown_pc=mspe_guest_return_pc(__builtin_return_address(0));' in s
assert 'g_diag_timer_set_pc=mspe_guest_return_pc(__builtin_return_address(0));' in s
assert 'g_diag_timer_set_param=(uint32_t)(uintptr_t)param;' in s
assert 'g_diag_timer_set_high=timeout_high;' in s
assert 'g_diag_event_key=key;' in s
assert 'if(g_timers[i].armed) armed++' in s
assert 'case 16: snprintf(out,cap,"tx:%lu sk:%lu ov:%lu"' in s
assert 'extern "C" int knl_set_timer(void *timer, uint32_t timeout_low,' in s
print('PASS: BackLight 4-register WIPI import and timer/event/PC diagnostics')
