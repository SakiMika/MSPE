#!/usr/bin/env python3
"""Host glyph/CP949 regression; independent of libnds (not a ROM runtime test)."""
from pathlib import Path
import subprocess, tempfile, textwrap
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT/'source/wipi_shim.cpp').read_text()
assert '#include "mspe_text_atlas.h"' in source
assert 'gfx_draw_string(uint32_t fbp,int x,int y,const uint8_t *s,int len,const WipiGraphicsContext *ctx)' in source
assert 'dst[py*stride+px]=fg;' in source
assert 'mspe_safe_text_length(s,len)' in source
assert 'return MspeText::measure(str,mspe_safe_text_length(str,len));' in source
assert 'g_diag_text_pixels' in source
cpp=textwrap.dedent(r'''
    #include "mspe_text_atlas.h"
    #include <assert.h>
    #include <stdint.h>
    int main() {
        const MspeText::Glyph* ascii=MspeText::find('A');
        assert(ascii && ascii->advance == 7);
        uint32_t pixels=0;
        for(int i=0;i<12;i++) pixels+=__builtin_popcount((unsigned)ascii->rows[i]);
        assert(pixels > 5);
        const unsigned char hangul[]={0xb8,0xde,0xc0,0xcc,0xc7,0xc3,0x00};
        int pos=0;
        const uint16_t a=MspeText::next(hangul,6,&pos);
        assert(a==0xb8de && pos==2 && MspeText::find(a));
        const uint16_t b=MspeText::next(hangul,6,&pos);
        assert(b==0xc0cc && pos==4 && MspeText::find(b));
        assert(MspeText::measure(hangul,-1)==36);
        const unsigned char latin[]="MAPLE";
        assert(MspeText::measure(latin,-1)==35);
        assert(MspeText::measure(latin,3)==21);
        assert(MspeText::measure(latin,-2)==0);
        assert(MspeText::find('?'));
        return 0;
    }
''')
with tempfile.TemporaryDirectory() as td:
    c=Path(td)/'test.cpp'; exe=Path(td)/'test'
    c.write_text(cpp)
    subprocess.run(['g++','-O2','-std=c++17','-Wall','-Wextra','-Werror',f'-I{ROOT/"source"}',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: CP949 Korean/ASCII decoding, atlas coverage, metrics, host build, source integration')
