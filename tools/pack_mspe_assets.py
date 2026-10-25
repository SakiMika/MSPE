#!/usr/bin/env python3
"""Copy original MapleStory Pirate Edition JAR members into NitroFS verbatim."""
from pathlib import Path
import argparse, zipfile
from pathlib import PurePosixPath
parser=argparse.ArgumentParser()
parser.add_argument('jar',type=Path)
parser.add_argument('--out',type=Path,default=Path('nitrofs'))
args=parser.parse_args()
with zipfile.ZipFile(args.jar) as z:
    files=[i for i in z.infolist() if not i.is_dir() and not i.filename.startswith('META-INF/')]
    for i in files:
        name=PurePosixPath(i.filename)
        if name.is_absolute() or '..' in name.parts: raise SystemExit('invalid member name')
        p=args.out.joinpath(*name.parts)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(z.read(i))
print(f'Copied {len(files)} original assets into {args.out}')
