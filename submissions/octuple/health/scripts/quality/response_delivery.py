#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, tempfile, unittest
from pathlib import Path
from toolkit_common import Parser, ToolError, atomic_write, emit, read_bytes, run
DEFAULT=Path("/logs/agent/response.txt")
def deliver(data,output):
    try: text=data.decode("utf-8")
    except UnicodeError as e: raise ToolError("draft must be UTF-8") from e
    if not text.strip(): raise ToolError("draft is empty")
    path=atomic_write(output,data); actual=path.read_bytes()
    if not actual or actual!=data: raise ToolError("delivery verification mismatch")
    return {"ok":True,"output":str(path),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"exact_match":True}
class T(unittest.TestCase):
    def test_delivery(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"out"; self.assertTrue(deliver("café".encode(),p)["exact_match"]); self.assertEqual(p.read_bytes(),"café".encode())
    def test_empty(self):
        with self.assertRaises(ToolError): deliver(b" ",Path("/tmp/x"))
def main():
    p=Parser(); p.add_argument("command",choices=("deliver","selftest")); p.add_argument("--draft"); p.add_argument("--output",type=Path,default=DEFAULT); a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    emit(deliver(read_bytes(a.draft),a.output)); return 0
if __name__=="__main__": raise SystemExit(run(main))
