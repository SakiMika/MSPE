#!/usr/bin/env python3
"""Host regression of actual MSPE DrawString and pending-pixel compositor."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/wipi_shim.cpp').read_text()
def extract(symbol):
    pos=s.index(symbol)
    brace=s.index('{',pos);depth=1;idx=brace+1
    while depth:
        if s[idx]=='{':depth+=1
        elif s[idx]=='}':depth-=1
        idx+=1
    return s[s.rfind('\n',0,pos)+1:idx]
code=r'''
#include "mspe_text_atlas.h"
#include "mspe_frame_compositor.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
struct WipiFramebuffer { uint32_t width,height,bpl,bpp,buf; };
struct WipiGraphicsContext { int32_t clip_x1,clip_y1,clip_x2,clip_y2;
    uint32_t foreground,background,alpha,pixel_op,pixel_param,font,style,xor_enabled;
    int32_t offset_x,offset_y; };
struct { uint32_t draw_string=0; } g_trace;
uint32_t g_diag_text_pixels=0,g_diag_text_skipped=0,g_diag_text_unknown=0;
uint32_t g_diag_last_text_fg=0,g_diag_last_text_fbp=0;
static bool valid_ptr(uint32_t a) { return a>=0x02000000u && a<0x04000000u; }
static WipiFramebuffer *as_fb(uint32_t addr) {return (WipiFramebuffer*)(uintptr_t)addr;}
static uint16_t *fb_pixels16(WipiFramebuffer *fb) {return (uint16_t*)(uintptr_t)fb->buf;}
uint16_t *g_phone_fb=nullptr;
static void mspe_offline_note_wait_text(const uint8_t*,int) {}
WipiFramebuffer g_screen_fb{};
static MspeFrame::PendingPixels g_screen_pending_pixels;
static uint32_t g_screen_overlay_dropped=0;
'''
for decl in ['static inline bool mspe_is_phone_fb(',
             'static inline void mspe_capture_pixel(const WipiFramebuffer *fb,int x,int y,uint16_t color) {',
             'static int mspe_safe_text_length(',
             'extern "C" int gfx_get_string_width(',
             'static uint32_t mspe_draw_text_pixels(',
             'extern "C" void gfx_draw_string(']:
    code+='\n'+extract(decl)+'\n'
code+=r'''
int main() {
    void *region=mmap((void*)0x02300000,0x50000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(region==(void*)0x02300000);
    auto *fb=(WipiFramebuffer*)region;
    fb->width=240;fb->height=320;fb->bpl=480;fb->bpp=16;fb->buf=0x02301000u;
    auto *pixels=(uint16_t*)(uintptr_t)fb->buf;
    g_phone_fb=pixels;
    g_screen_fb=*fb;
    auto *txt=(uint8_t*)0x02340000;
    memcpy(txt,"MAPLE",6);
    WipiGraphicsContext ctx{};
    ctx.clip_x1=0;ctx.clip_y1=0;ctx.clip_x2=239;ctx.clip_y2=319;
    for(int i=0;i<240*320;i++) pixels[i]=0xffff;
    gfx_draw_string(0x02300000,10,70,txt,-1,&ctx);
    unsigned dark=0;
    for(int y=70;y<82;y++) for(int x=10;x<45;x++) if(pixels[y*240+x]!=0xffff) ++dark;
    assert(dark>=20 && g_diag_text_pixels==dark);
    assert(pixels[0]==0xffff);
    assert(gfx_get_string_width(12,txt,-1)==35);
    // Capture glyphs, then simulate offscreen framebuffer replacing phone.
    for(int i=0;i<240*320;i++) pixels[i]=0xffff;
    assert(g_screen_pending_pixels.restore(pixels,240)==dark);
    unsigned restored=0;
    for(int y=70;y<82;y++)for(int x=10;x<45;x++) if(pixels[y*240+x]==0) ++restored;
    assert(restored==dark && pixels[0]==0xffff);
    ctx.clip_x1=20;ctx.clip_x2=30;
    for(int i=0;i<240*320;i++) pixels[i]=0xffff;
    gfx_draw_string(0x02300000,10,70,txt,-1,&ctx);
    unsigned inside=0,outside=0;
    for(int y=70;y<82;y++)for(int x=10;x<45;x++)if(pixels[y*240+x]!=0xffff){
        if(x>=20&&x<=30)++inside; else ++outside;
    }
    assert(inside>0&&outside==0);
    g_screen_pending_pixels.discard();
    ctx.clip_x1=0;ctx.clip_x2=239;ctx.foreground=0xf800;
    txt[0]=0xb8;txt[1]=0xde;txt[2]=0;
    gfx_draw_string(0x02300000,70,100,txt,-1,&ctx);
    assert(gfx_get_string_width(12,txt,-1)==12);
    unsigned korean=0;
    for(int y=100;y<112;y++)for(int x=70;x<82;x++)if(pixels[y*240+x]==0xf800) korean++;
    assert(korean>10);
    assert(g_diag_text_skipped==0&&g_diag_text_unknown==0);
    munmap(region,0x50000);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as td:
    f=Path(td)/'draw.cpp';exe=Path(td)/'draw';f.write_text(code)
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',f'-I{ROOT/"source"}',str(f),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: actual DrawString pixels, clipping, CP949 and pixel-snapshot flush')
