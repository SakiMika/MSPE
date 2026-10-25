#!/usr/bin/env python3
"""Verify guest-specific four-register WIPI-C timer ABI and host shim logic.

This test checks original ELF Thumb operands, not merely assertions about our
own source. It cannot replace an ARM9 build or an emulator runtime check.
"""
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
src = (root / 'source/wipi_shim.cpp').read_text()
elf = (root / 'nitrofs/binary.mod').read_bytes()
assert elf[:4] == b'\x7fELF', 'original guest payload missing'
text_vaddr = 0x1000
text_off = 0x34

def thumb16(addr):
    return struct.unpack_from('<H', elf, text_off + addr - text_vaddr)[0]

# Original MapleStory wrapper at 0x1A90 passes a signed 64-bit delay and a
# separate context pointer: r1=low r2=high r3=context. 0x1F38 timer callback
# tests the second argument and returns early when that pointer is NULL.
assert thumb16(0x1a96) == 0x17e5, 'expected ASRS r5,r4,#31 (upper word)'
assert thumb16(0x1aa0) == 0x1c2a, 'expected MOVS r2,r5 (upper word)'
assert thumb16(0x1aa6) == 0x1c33, 'expected MOVS r3,r6 (callback param)'
assert thumb16(0x1f40) == 0x2900, 'expected CMP r1,#0 in timer callback'

pattern = (r'extern "C" int knl_set_timer\(void \*timer, uint32_t timeout_low,\s*'
           r'uint32_t timeout_high, void \*param\)\s*\{')
m = re.search(pattern, src)
assert m, 'MC_knlSetTimer must preserve timer, low, high, and callback param'
assert 'case 0x7b: fn=(void*)knl_set_timer;' in src
assert '((uint64_t)timeout_high << 32) | timeout_low' in src
assert 'g_diag_timer_set_param=(uint32_t)(uintptr_t)param;' in src
assert 'g_diag_timer_set_high=timeout_high;' in src
assert 'g_diag_timer_param=(uint32_t)(uintptr_t)param' in src

# Compile the actual implementation extracted from source against host
# bookkeeping fixtures. A test-only function would not exercise the patch.
pos = src.index('{', m.start())
depth = 0
end = None
for i in range(pos, len(src)):
    if src[i] == '{':
        depth += 1
    elif src[i] == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
assert end
fn = src[m.start():end]
harness = r'''#include <cassert>
#include <cstdint>
#include <cstdio>
#include <climits>
struct TimerSlot {
    void* timer;
    void (*callback)(void*,void*);
    void* param;
    uint64_t due_ms;
    bool armed;
};
constexpr int TIMER_SLOTS=32;
static TimerSlot g_timers[TIMER_SLOTS]{};
struct { unsigned timer_set=0; } g_trace;
static unsigned g_timer_trace_budget=0;
static uint64_t g_test_now=1000;
static uint64_t timer_now_ms(){ return g_test_now; }
static uint32_t g_diag_timer_set_pc=0;
static uint32_t g_diag_timer_set_delay=0;
static uint32_t g_diag_timer_set_high=0;
static uint32_t g_diag_timer_set_param=0;
static uint32_t mspe_guest_return_pc(void*) { return 0; }
''' + fn + r'''
int main(){
    int timer=7, cookie=99, another=100;
    g_timers[0].timer=&timer;
    assert(knl_set_timer(&timer,33,0,&cookie)==0);
    assert(g_timers[0].param==&cookie);
    assert(g_timers[0].due_ms==1033 && g_timers[0].armed);
    assert(g_diag_timer_set_delay==33 && g_diag_timer_set_high==0);
    // WIPI-C reports an already armed timer rather than silently replacing it.
    assert(knl_set_timer(&timer,44,0,&another)==-5);
    assert(g_timers[0].param==&cookie && g_timers[0].due_ms==1033);
    g_timers[0].armed=false;
    assert(knl_set_timer(&timer,0,1,&another)==0);
    assert(g_timers[0].param==&another);
    assert(g_timers[0].due_ms == 1000ull+(1ull<<32));
    g_timers[0].armed=false;
    g_test_now=UINT64_MAX-10;
    assert(knl_set_timer(&timer,100,0,&cookie)==0);
    assert(g_timers[0].due_ms==UINT64_MAX);
    assert(g_trace.timer_set==3);
    assert(knl_set_timer(&another,10,0,&cookie)==-25);
}
'''
compiler = shutil.which('g++') or shutil.which('clang++')
if compiler:
    with tempfile.TemporaryDirectory() as td:
        code = Path(td)/'timer.cpp'
        out = Path(td)/'test_timer'
        code.write_text(harness)
        subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror',str(code),'-o',str(out)],check=True)
        subprocess.run([str(out)],check=True)
    print('PASS: original guest Thumb call, 4-register ABI, host timer behavior')
else:
    print('PASS: guest Thumb and 4-register ABI source checks (no host C++ compiler)')
