#!/usr/bin/env python3
"""Static + behavioral checks for Violet defaults and intentionally unused SELECT.
These checks don't replace a devkitARM ROM build or hardware test.
"""
from pathlib import Path
import re
p=Path(__file__).resolve().parents[1]
s=(p/'source/wipi_shim.cpp').read_text()
m=(p/'source/main.cpp').read_text()
body=s[s.index('static void runner_ui_defaults(void) {'):s.index('static uint32_t runner_first_physical(',s.index('static void runner_ui_defaults(void) {'))]
def assn(name):
    return {int(i):v for i,v in re.findall(rf'\b{name}\[(\d+)\]\s*=\s*(KEY_[A-Z]+)',body)}
assert assn('g_ui_single_map')=={0:'KEY_A',1:'KEY_B',7:'KEY_Y',8:'KEY_X',9:'KEY_R',10:'KEY_START'}
assert 'const int targets[4]={2,3,5,6};' in body
assert 'const uint32_t keys[4]={KEY_A,KEY_B,KEY_X,KEY_Y};' in body
assert 'g_ui_combo_map1[targets[i]]=KEY_L;' in body
assert 'g_ui_combo_map2[targets[i]]=keys[i];' in body
assert 'g_ui_combo_map1[1]=KEY_L' not in body
assert 'g_ui_combo_map2[1]=KEY_START' not in body
assert 'g_bottom_half_visible=true;' in body
physical=s[s.index('static const uint32_t g_runner_physical_keys[]'):s.index('constexpr int UI_PHYSICAL_COUNT')]
assert 'KEY_SELECT' not in physical and '"SELECT"' not in physical
keys=s[s.index('void wipi_dispatch_keys('):s.index('constexpr int UI_QUICK_H',s.index('void wipi_dispatch_keys('))] if 'constexpr int UI_QUICK_H' in s[s.index('void wipi_dispatch_keys('):] else s[s.index('void wipi_dispatch_keys('):]
assert '~(KEY_TOUCH|KEY_LID|KEY_SELECT)' in keys
assert 'if((down&KEY_SELECT)' not in keys
assert 'g_bottom_half_visible=!' not in keys
assert 'activeComboPhysical|=need' in keys and '!(activeComboPhysical&key)' in keys
assert 'call_event(502,wipi)' in keys and 'call_event(503,wipi)' in keys
assert 'X=0' in m and 'A=EZ' in m and 'B=CLR' in m
assert 'SELECT=unused' in m
# Simulate unmodified Violet single/combination physical-to-logical translation.
single={ 'A':-5, 'B':-16, 'X':ord('0'), 'Y':ord('*'), 'R':ord('#'), 'START':-10 }
combos={ 'A':ord('1'),'B':ord('3'),'X':ord('7'),'Y':ord('9') }
def emitted(held):
    if 'L' in held:
        consumed=set(held)&set(combos)
        out={combos[k] for k in consumed}
    else:
        consumed=set();out=set()
    out.update(v for k,v in single.items() if k in held and k not in consumed)
    out.update({'UP':-1,'DOWN':-2,'LEFT':-3,'RIGHT':-4}[k] for k in ('UP','DOWN','LEFT','RIGHT') if k in held)
    return out
for physical,wipi in single.items():
    assert emitted({physical})=={wipi}
for physical,wipi in combos.items():
    assert emitted({'L',physical})=={wipi}
assert emitted({'SELECT'})==set()
assert emitted({'SELECT','A'})=={-5}
assert emitted({'L'})==set()
assert emitted({'UP','A'})=={-1,-5}
print('PASS: VioletDS default mappings; L suppresses singles; SELECT unused; main UI labels updated.')
