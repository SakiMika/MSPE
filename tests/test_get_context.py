#!/usr/bin/env python3
"""Host-test the actual 1FB:0CF GetContext ABI against WIE LGT contract."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/wipi_shim.cpp').read_text()
pos=s.index('extern "C" int gfx_get_context(')
brace=s.index('{',pos);depth=1;i=brace+1
while depth:
    if s[i]=='{':depth+=1
    elif s[i]=='}':depth-=1
    i+=1
code=r'''
#include <stdint.h>
#include <assert.h>
#include <sys/mman.h>
struct WipiGraphicsContext { int32_t clip_x1,clip_y1,clip_x2,clip_y2;
    uint32_t foreground,background,alpha,pixel_op,pixel_param,font,style,xor_enabled;
    int32_t offset_x,offset_y; };
static bool valid_ptr(uint32_t p) {return p>=0x02000000u&&p<0x04000000u;}
'''+s[pos:i]+r'''
int main() {
    void *m=mmap((void*)0x02300000,0x1000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(m==(void*)0x02300000);
    auto *ctx=(WipiGraphicsContext*)m;
    auto *out=(uint32_t*)0x02300100u;
    ctx->clip_x1=2;ctx->clip_y1=3;ctx->clip_x2=101;ctx->clip_y2=199;
    ctx->foreground=0xA5A5;ctx->background=0xBEEF;ctx->alpha=127;
    ctx->font=13;ctx->style=2;ctx->offset_x=-5;ctx->offset_y=9;
    assert(gfx_get_context(ctx,0,0x02300100u)==0);
    assert(out[0]==2&&out[1]==3&&out[2]==102&&out[3]==200);
    assert(gfx_get_context(ctx,1,0x02300100u)==0&&out[0]==0xA5A5);
    assert(gfx_get_context(ctx,2,0x02300100u)==0&&out[0]==0xBEEF);
    assert(gfx_get_context(ctx,4,0x02300100u)==0&&out[0]==127);
    assert(gfx_get_context(ctx,7,0x02300100u)==0&&out[0]==13);
    assert(gfx_get_context(ctx,8,0x02300100u)==0&&out[0]==2);
    assert(gfx_get_context(ctx,10,0x02300100u)==0&&out[0]==(uint32_t)-5&&out[1]==9);
    out[0]=0x12345678;
    assert(gfx_get_context(ctx,99,0x02300100u)==0&&out[0]==0x12345678);
    assert(gfx_get_context(ctx,0,0)==-9);
    assert(gfx_get_context(ctx,0,0x03FFFFFEu)==-9);
    assert(gfx_get_context(ctx,0,0x02300100u)==0);
    munmap(m,0x1000);
    return 0;
}
'''
assert 'case 0xcf: fn=(void*)gfx_get_context; break;' in s
with tempfile.TemporaryDirectory() as td:
    f=Path(td)/'test.cpp';exe=Path(td)/'test';f.write_text(code)
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(f),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: LGT 0xCF GetContext bounds, clipboard, flags, fonts, offsets')
