#!/usr/bin/env python3
"""Regression: compile real extracted WIPI-C network shim functions on host.
No emulator/device/network or devkitARM required. The 32-bit callback ABI is
exercised in a non-PIE host executable with fixed low-code addresses.
"""
import re
import subprocess
import tempfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
src=(root/'source/wipi_shim.cpp').read_text()

# Use the actual source code rather than a separate reimplementation.
def function(name):
    match=re.search(r'(?m)^(?:extern "C" )?(?:static )?\w+(?: \*|\s+)'+re.escape(name)+r'\s*\(',src)
    assert match, name
    start=match.start()
    brace=src.index('{',match.end())
    depth=0
    for pos in range(brace,len(src)):
        if src[pos]=='{': depth+=1
        elif src[pos]=='}':
            depth-=1
            if depth==0: return src[start:pos+1]
    raise AssertionError(name)

state=src[src.index('struct MspeOfflineNetFailure {'):src.index('static MspeOfflineNetFailure g_offline_net{};')+len('static MspeOfflineNetFailure g_offline_net{};')]
names=['mspe_net_callback_address','mspe_net_connect','mspe_net_close','mspe_net_socket','mspe_net_socket_connect',
    'mspe_net_socket_write','mspe_net_socket_read','mspe_net_socket_close',
    'mspe_net_set_read_callback','mspe_net_set_write_callback','mspe_poll_offline_network']
for number,name in {0x258:'mspe_net_connect',0x259:'mspe_net_close',0x25a:'mspe_net_socket',
  0x25b:'mspe_net_socket_connect',0x25c:'mspe_net_socket_write',0x25d:'mspe_net_socket_read',
  0x25e:'mspe_net_socket_close',0x265:'mspe_net_set_read_callback',
  0x266:'mspe_net_set_write_callback'}.items():
    assert f'case 0x{number:x}: fn=(void*){name}; break;' in src,(number,name)
assert src.index('mspe_poll_offline_network();') < src.index('process_timers();',src.index('void wipi_poll(void)'))

boilerplate=r'''
#include <cstdint>
#include <cstdio>
#include <cassert>
#define ZEN_CONSERVATIVE_CALLBACK_CACHE 0
static bool valid_ptr(uint32_t p) { return p>=0x400000u && p<0x800000u; }
static uintptr_t g_guest_text_new=0;
static uint32_t g_guest_text_old=0;
static uint32_t g_guest_text_size=0;
static unsigned called=0;
static int last_status=0;
static uint32_t last_param=0;
static void callback(int status, uint32_t param) {
    called++;last_status=status;last_param=param;
}
'''

test=r'''
int main() {
    uint32_t cb=(uint32_t)(uintptr_t)&callback;
    assert(valid_ptr(cb));
    assert(mspe_net_connect(cb,0x12345678)==0);
    assert(called==0); // asynchronous API, must not reenter callback in connect
    assert(mspe_net_connect(cb,0)==-5);
    assert(mspe_net_close()==0);
    mspe_poll_offline_network();
    assert(called==1 && last_status==-1 && last_param==0x12345678);
    mspe_poll_offline_network();
    assert(called==1); // never callback twice
    assert(mspe_net_connect(cb,777)==0);
    mspe_poll_offline_network();
    assert(called==2 && last_status==-1 && last_param==777);
    assert(mspe_net_socket(2,1)==-1);
    assert(mspe_net_socket_connect(0,0,0,0,0)==-1);
    assert(mspe_net_socket_write(0,nullptr,1)==-1);
    assert(mspe_net_socket_read(0,nullptr,1)==-1);
    assert(mspe_net_socket_close(0)==-1);
    assert(mspe_net_set_read_callback(0,0,0)==-1);
    assert(mspe_net_set_write_callback(0,0,0)==-1);
    assert(g_offline_net.requests==3 && g_offline_net.failures==2);
}
'''
cpp=boilerplate+'\n'+state+'\n'+'\n\n'.join(function(x) for x in names)+'\n'+test
with tempfile.TemporaryDirectory() as t:
    p=Path(t)/'test.cpp';p.write_text(cpp)
    exe=Path(t)/'test'
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-fno-pie','-no-pie',str(p),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=10)
print('PASS: actual WIPI network bridge deferred -1 callback; sockets fail immediately; no repeated callback')
