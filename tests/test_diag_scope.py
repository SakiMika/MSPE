#!/usr/bin/env python3
"""Guard v08: match global diagnostic declarations and retain clean TOP screen.

This is a source-level regression test; it is not a devkitARM compile test.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
text = (root / "source" / "wipi_shim.cpp").read_text()
namespace = text.index("namespace {")
namespace_end = text.index("\n}\n\nuint32_t zen_boot_clock_ms")
before = text[:namespace]
inside = text[namespace:namespace_end]
after = text[namespace_end:]
for name in ("mspe_diag_mark", "mspe_diag_line"):
    decl = re.compile(r"^static void " + name + r"\([^;{}]*\);$", re.M)
    definition = re.compile(r"^static void " + name + r"\([^;{}]*\)\s*\{", re.M)
    assert len(decl.findall(before)) == 1, name + ": requires one global declaration"
    assert not decl.search(inside), name + ": duplicate prototype inside anonymous namespace"
    assert len(definition.findall(after)) == 1, name + ": requires one global definition"
print("PASS: MSPE bottom-only diagnostic helpers have matching declarations/definitions.")

assert 'mspe_diag_render' not in text, "TOP overlay helper must not exist"
assert 'probe_rect' not in text and 'probe_text' not in text, "old TOP debug rasterizer must be removed"
