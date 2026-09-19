#!/usr/bin/env python3
from __future__ import annotations
import unittest
from toolkit_common import Parser, ToolError, emit, read_json, run
def check(v):
    if not isinstance(v,dict) or not isinstance(v.get("actions"),list): raise ToolError("actions must be an array")
    issues=[]; labels=set()
    for i,a in enumerate(v["actions"]):
        if not isinstance(a,dict): raise ToolError("each action must be an object")
        for field in ("level","action","timeframe"):
            if not isinstance(a.get(field),str) or not a[field].strip(): issues.append(f"action {i} missing {field}")
        triggers=a.get("triggers")
        if not isinstance(triggers,list) or not triggers or not all(isinstance(x,str) and x.strip() for x in triggers): issues.append(f"action {i} needs trigger strings")
        label=a.get("level")
        if label in labels: issues.append(f"duplicate level: {label}")
        labels.add(label)
    return {"ok":not issues,"issues":issues,"mapping_agent_provided":True,"triage_decision_made":False,"instruction":"Structure only; manually verify action, timing, and triggers."}
class T(unittest.TestCase):
    def test(self): self.assertTrue(check({"actions":[{"level":"one","action":"contact","timeframe":"stated time","triggers":["stated change"]}]})["ok"])
    def test_missing(self): self.assertFalse(check({"actions":[{}]})["ok"])
def main():
    p=Parser(); p.add_argument("command",choices=("check","selftest")); p.add_argument("--input"); a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    emit(check(read_json(a.input))); return 0
if __name__=="__main__": raise SystemExit(run(main))
