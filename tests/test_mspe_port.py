#!/usr/bin/env python3
"""Static validation; DOES NOT claim NDS ROM was compiled or game booted."""
from pathlib import Path
import struct, hashlib, sys, re
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_imports import report

repo={p.relative_to(ROOT/'nitrofs').as_posix():p for p in (ROOT/'nitrofs').rglob('*') if p.is_file()}
assert len(repo)==654,len(repo)  # 653 inner-JAR files + 1 original outer-ZIP certificate
assert repo['certification'].read_bytes()==b'01000000000\x00' 
assert sum(p.stat().st_size for p in repo.values())==2743608
checksums=(ROOT/'tests/asset_checksums.txt').read_text().splitlines()
assert len(checksums)==len(repo)-1  # preserve 653 original inner-JAR checksums
for line in checksums:
    expected,relative=line.split('  ',1)
    assert relative in repo,relative
    assert hashlib.sha256(repo[relative].read_bytes()).hexdigest()==expected,relative
binary=repo['binary.mod'].read_bytes()
assert binary.startswith(b'\x7fELF') and len(binary)==1440424
assert struct.unpack_from('<I',binary,0x18)[0]==0x55000
imp,keys,hits,miss=report()
assert len(imp)==175,len(imp)
assert (0x1fb,0x03) in hits,'CletRegister must be implemented'
assert (0x1fb,0x80) in hits and (0x1fb,0x81) in hits,'Resource API missing'
assert (0x1fb,0xca) in hits,'Screen framebuffer API missing'
assert (0x1fb,0xde) in hits,'FlushLCD missing'
assert (0x1fb,0x7a) in hits and (0x1fb,0x7b) in hits,'Timer APIs missing'
# Missing methods are intentionally reported, not silently labeled compatible.
assert miss,'This first-pass bridge is not ABI-complete'
main=(ROOT/'source/main.cpp').read_text()
shim=(ROOT/'source/wipi_shim.cpp').read_text()
make=(ROOT/'Makefile').read_text()
header=(ROOT/'tools/patch_nds_header.py').read_text()
assert 'wipi_start_clet()' in main and 'lgt_load_binary_memory' in main
assert 'prepatch_lgt_imports(&image)' in main
assert '0x000027D8u' not in main and '0x0000B110u' not in main
assert 'wipi_set_ragnarok_ez_bridge' not in main+shim
assert 'call_event(502,wipi)' in shim and 'call_event(503,wipi)' in shim
assert 'constexpr int HALF_H=PHONE_H/2' in shim
assert 'copy_phone_rect_to_ds_buf(g_sub_comp,0,0,PHONE_W,HALF_H,DST_X,TOP_DST_Y)' in shim
assert 'copy_phone_rect_to_ds_buf(g_sub_comp,0,HALF_H,PHONE_W,HALF_H,DST_X,SUB_DST_Y)' in shim
assert 'MspeSav::' in shim and 'ZenSav::' not in shim
# Runtime diagnostics are retained on SUB LOG, never on TOP.
assert 'mspe_diag_mark("IN TIMER")' in shim
assert 'mspe_diag_mark("IN PAINT")' in shim
assert 'mspe_diag_mark("IN EVENT")' in shim
assert 'mspe_diag_render' not in shim
assert 'unk:%03lX:%03lX pc:%08lX' in shim and 'PIX WHITE:' not in shim
assert 'const char *s="0002A4F0"' in shim
assert 'uint32_t red_mask;\n    uint32_t green_mask;\n    uint32_t blue_mask;' in shim
assert 'if(!gfx_flush_source_to_phone(source))' in shim
assert 'TARGET      := MSPE' in make
assert '-g "MSPE"' in make
assert "PROFILE_GAMECODE = b'MSPE'" in header
assert "b'MAPLESTORYPE'" in header
assert 'MSPE_*.sav' in (ROOT/'source/mspe_sav_backend.cpp').read_text()
# Catch broken source-to-source include dependencies before attempting a full
# devkitARM build. This would have caught the missing zen_map_art.h in v1.
for src in sorted((ROOT/'source').rglob('*')):
    if not src.is_file() or src.suffix not in ('.cpp', '.c', '.h', '.hpp'):
        continue
    for lineno, text in enumerate(src.read_text().splitlines(), 1):
        match = re.match(r'\s*#\s*include\s*"([^"]+)"', text)
        if match:
            dependency = src.parent / match.group(1)
            assert dependency.is_file(), f'{src.relative_to(ROOT)}:{lineno}: missing {match.group(1)}'
assert '#include "mspe_runner_ui.h"' in shim
assert 'MspeRunnerUI::gear(' in shim
assert not (ROOT/'source/zen_map_ui.h').exists()

icon=(ROOT/'icon.bmp').read_bytes()
assert icon[:2]==b'BM'
assert struct.unpack_from('<ii',icon,18)==(32,32)
assert struct.unpack_from('<H',icon,28)[0]==8 # 16-color indexed BMP
print('PASS: MSPE ELF, pristine assets, prepatch loader, keymap, display split, save isolation, header ID.')
print('NOTE: static PASS does not establish successful compile/boot or working gameplay.')
