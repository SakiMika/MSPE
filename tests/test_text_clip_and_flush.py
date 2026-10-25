#!/usr/bin/env python3
"""Regress WIPI clip ABI and safe pixel-snapshot FlushLcd composition."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'source/wipi_shim.cpp').read_text()
assert 'ctx->clip_x2=v[2] - 1; ctx->clip_y2=v[3] - 1;' in s
assert 'ctx->clip_x2=v[0] + v[2] - 1' not in s
assert 'if(sp==g_phone_fb) { g_screen_pending_pixels.discard(); return true; }' in s
assert 'g_screen_pending_pixels.restore(g_phone_fb,PHONE_W);' in s
assert 'g_screen_pending_pixels.write(x,y,color)' in s
assert 'mspe_capture_row(dst,dx+left,dy+yy,out,right-left);' in s
assert 'mspe_capture_pixel(fb,px,py,fg);' in s
assert 'mspe_record_screen_draw_image' not in s
assert 'MspeScreenOverlayOp' not in s
assert 'mspe_frame_compositor.h' in s
print('PASS: LGT clip bounds and pixel-exact FlushLcd preservation; no stale image handles')
