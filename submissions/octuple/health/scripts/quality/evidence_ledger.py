#!/usr/bin/env python3
from __future__ import annotations
import argparse, unittest, unicodedata
from toolkit_common import Parser, ToolError, emit, read_json, run
STATES=("reported","explicitly_denied","unassessed")
def check(v):
    if not isinstance(v,dict) or set(v)!=set(STATES): raise ToolError("expected exactly three evidence states")
    seen={}; original={}
    for state in STATES:
        if not isinstance(v[state],list) or not all(isinstance(x,str) for x in v[state]): raise ToolError(f"{state} must be a string array")
        for item in v[state]:
            key=" ".join(unicodedata.normalize("NFC",item).casefold().split())
            if key: seen.setdefault(key,set()).add(state); original.setdefault(key,item)
    conflicts=[{"item":original[k],"states":sorted(s)} for k,s in sorted(seen.items()) if len(s)>1]
    return {"ok":not conflicts,"conflicts":conflicts,"state_counts":{s:len(v[s]) for s in STATES},"semantic_truth_verified":False}
class T(unittest.TestCase):
    def test_conflict(self): self.assertFalse(check({"reported":["No fever"],"explicitly_denied":[" no  FEVER "],"unassessed":[]})["ok"])
    def test_clear(self): self.assertTrue(check({s:[] for s in STATES})["ok"])
def main():
    p=Parser(); p.add_argument("command",choices=("check","selftest")); p.add_argument("--input") ; a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    emit(check(read_json(a.input))); return 0
if __name__=="__main__": raise SystemExit(run(main))
