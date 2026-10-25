#!/usr/bin/env python3
"""Static audit of WIPI guest thunk imports and implemented libnds bridge entries.

Matches the exact ARM import veneers used by the supplied WIPI ELF (no guesses
about indirect imports or dynamic runtime feature support). An import linked to
a shim function is NOT proof the game's ABI and behavior are fully supported.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import re, struct, argparse

ROOT=Path(__file__).resolve().parents[1]

def imports(data: bytes):
    if data[:4]!=b'\x7fELF':
        raise ValueError('invalid ELF')
    result=[]
    for i in range(0x34,len(data)-16,4):
        op0,op1,tbl,method=struct.unpack_from('<IIII',data,i)
        if op0==0xe52de004 and (op1&0xff000000)==0xeb000000 and tbl in (0x1fb,0x1f8,1):
            result.append((tbl,method,i))
    return result

def mapped(source:str):
    mapped=set()
    # These two scopes contain all direct WIPI and standard-library table entries.
    wipic=source.split('if(table==0x1fb) {',1)[1].split('} else if(table==0x1f8',1)[0]
    std=source.split('} else if(table==1) {',1)[1].split('\n    if(fn)',1)[0]
    for t,chunk in ((0x1fb,wipic),(1,std)):
        mapped.update((t,int(x,16)) for x in re.findall(r'case 0x([0-9A-Fa-f]+)\s*:',chunk))
    if 'table==0x1f8 && index==0x16' in source: mapped.add((0x1f8,0x16))
    return mapped

def report():
    imp=imports((ROOT/'nitrofs/binary.mod').read_bytes())
    supported=mapped((ROOT/'source/wipi_shim.cpp').read_text())
    keys={(t,i) for t,i,_ in imp}
    hits={k for k in keys if k in supported}
    unhandled=sorted(keys-hits)
    print(f'MSPE ARM ELF: {len(imp)} import veneers; {len(keys)} unique (table,index) pairs')
    print(f'Shim method bindings: {len(hits)} unique; fallback stubs: {len(unhandled)} unique')
    print('Referenced import counts by table:',dict(Counter(hex(t) for t,_,_ in imp)))
    for table in (0x1fb,0x1f8,1):
        items=[ix for t,ix in unhandled if t==table]
        print(f'Unmapped table {table:03X}: {len(items)} methods '+ ' '.join(f'{n:03X}' for n in items))
    return imp,keys,hits,unhandled

if __name__=='__main__':
    report()
