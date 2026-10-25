#!/usr/bin/env python3
"""v15 regression: detect the actual MSPE wait caption and bound key recovery.

This test intentionally does not claim to exercise the full ARM9 event loop.
"""
from pathlib import Path
import re, subprocess, tempfile
s=(Path(__file__).resolve().parents[1]/'source/wipi_shim.cpp').read_text()
assert 'mspe_poll_offline_network();\n    mspe_poll_offline_wait_guard();\n    process_timers();' in s
assert 'if(g_offline_wait.attempts>=3) return;' in s
assert 'call_event(502,-16);' in s and 'call_event(503,-16);' in s
assert 'mspe_offline_note_wait_text(s,n)' in s
assert 'mspe_net_callback_address(callback)' in s
assert 'case 0x258: fn=(void*)mspe_net_connect; break;' in s
assert 'fn(-1, param)' in s
beg=s.index('static const uint8_t mspe_online_wait_cp949[]')
end=s.index('static void mspe_offline_note_wait_text(',beg)
code=s[beg:end]
test='''
#include <cstdint>
#include <cstring>
#include <cassert>
'''+code+'''
int main() {
    const uint8_t original[]={0xb3,0xd7,0xc6,0xae,0xbf,0xf7,0x20,
         0xc1,0xa2,0xbc,0xd3,0xc1,0xdf,0x27,0x00};
    assert(mspe_offline_is_wait_text(original,sizeof(original)));
    const uint8_t text[]="NORMAL GAME DIALOG";
    assert(!mspe_offline_is_wait_text(text,sizeof(text)));
    const uint8_t not_full[]={0xb3,0xd7,0xc6,0xae};
    assert(!mspe_offline_is_wait_text(not_full,sizeof(not_full)));
    return 0;
}
'''
with tempfile.TemporaryDirectory() as t:
    cpp=Path(t)/'test.cpp'; exe=Path(t)/'test';cpp.write_text(test)
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: exact Korean wait caption, bounded CLR fallback, WIPI error path')
