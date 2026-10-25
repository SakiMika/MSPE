#!/usr/bin/env python3
"""Run actual NDS compositor class on host: compositing must be pixel-exact."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
code=r'''
#include "mspe_frame_compositor.h"
#include <cassert>
#include <cstring>
int main() {
    MspeFrame::PendingPixels overlay;
    uint16_t screen[320][240]{};
    assert(!overlay.pending());
    assert(!overlay.write(-1,0,1234));
    assert(!overlay.write(240,0,1234));
    assert(overlay.write(20,50,0x1234));
    assert(overlay.write(20,50,0xABCD)); // same pixel, last writer wins
    uint16_t input[]={1,2,3,4};
    overlay.writeRow(0,100,input,4);
    overlay.writeRow(-2,101,input,4); // correct clipping for row
    std::memset(screen,0xff,sizeof(screen));
    assert(overlay.restore(&screen[0][0],240)==7);
    assert(screen[50][20]==0xABCD);
    assert(screen[50][21]==0xFFFF); // untouched background is unchanged
    for(int i=0;i<4;i++) assert(screen[100][i]==input[i]);
    assert(screen[101][0]==3 && screen[101][1]==4);
    assert(!overlay.pending());
    assert(overlay.restore(&screen[0][0],240)==0);
    assert(overlay.write(12,7,0x1987));
    overlay.discard();  // in-place flush needs no replay
    assert(!overlay.pending());
    assert(overlay.restore(&screen[0][0],240)==0);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as td:
    f=Path(td)/'test.cpp'; exe=Path(td)/'test'
    f.write_text(code)
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',f'-I{root/"source"}',str(f),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: compositor pixel capture, row clipping, last write, flush and discard')
