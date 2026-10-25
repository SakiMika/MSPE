from pathlib import Path
import hashlib, re
BASE=Path(__file__).resolve().parent.parent
cert=(BASE/'nitrofs'/'certification').read_bytes()
assert cert == b'01000000000\x00', repr(cert)
s=(BASE/'source'/'wipi_shim.cpp').read_text()
assert 'v="01000000000"' in s
assert 'load=db_load_persistent(d,name)' in s
assert 'offline_cert=strcmp(name,"certification")==0' in s
assert 'd.packaged=false;' in s
assert 'if(mode!=4)' in s
assert 'if(mode==1)' in s
assert 'const bool offline_cert=' in s
assert 'case 0x258: fn=(void*)mspe_net_connect; break;' in s
assert 'fn(-1, param)' in s # explicitly report failure; never fake a server success
print('PASS: original certificate, phone identity, DB seed/restore, explicit failed network callback')
