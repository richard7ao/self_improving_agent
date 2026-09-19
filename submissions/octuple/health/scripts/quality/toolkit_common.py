#!/usr/bin/env python3
"""Internal stdlib helpers for response_tools. Not a learner-facing command."""
from __future__ import annotations
import argparse, json, os, sys, tempfile
from pathlib import Path

MAX_BYTES = 1_000_000

class ToolError(Exception): pass
class Parser(argparse.ArgumentParser):
    def error(self, message):
        emit({"ok":False,"error":"usage","detail":message}); raise SystemExit(2)

def emit(value): print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
def read_bytes(path=None):
    if path in (None,"-"): data=sys.stdin.buffer.read(MAX_BYTES+1)
    else:
        with Path(path).open("rb") as handle: data=handle.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES: raise ToolError(f"input exceeds {MAX_BYTES} bytes")
    return data
def read_text(path=None):
    try: return read_bytes(path).decode("utf-8")
    except UnicodeError as e: raise ToolError("input must be UTF-8") from e
def read_json(path=None):
    try: return json.loads(read_text(path))
    except json.JSONDecodeError as e: raise ToolError(f"invalid JSON: {e}") from e
def canonical(value): return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
def atomic_write(path, data):
    path=Path(path)
    if not path.is_absolute() or path.is_symlink() or path.parent.is_symlink(): raise ToolError("unsafe output path")
    parent=path.parent.resolve(strict=False); parent.mkdir(parents=True,exist_ok=True); path=parent/path.name
    fd,tmp=tempfile.mkstemp(prefix=f".{path.name}.",suffix=".tmp",dir=parent); temp=Path(tmp)
    try:
        with os.fdopen(fd,"wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temp,path)
    except BaseException: temp.unlink(missing_ok=True); raise
    return path
def run(main):
    try: return main()
    except ToolError as e: emit({"ok":False,"error":"input","detail":str(e)}); return 3
    except OSError as e: emit({"ok":False,"error":"io","detail":str(e)}); return 4
