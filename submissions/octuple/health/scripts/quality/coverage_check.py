#!/usr/bin/env python3
from __future__ import annotations
import unittest
from toolkit_common import Parser, ToolError, emit, read_json, run
def strings(v,name):
    if not isinstance(v,list) or not all(isinstance(x,str) and x for x in v): raise ToolError(f"{name} must be nonempty strings")
    return v
def check(v):
    if not isinstance(v,dict) or not isinstance(v.get("text"),str): raise ToolError("text must be a string")
    folded=v["text"].casefold(); concepts=v.get("required_concepts",[]); clauses=strings(v.get("required_clauses",[]),"required_clauses")
    found=[]; missing=[]
    if not isinstance(concepts,list): raise ToolError("required_concepts must be an array")
    for c in concepts:
        if not isinstance(c,dict) or not isinstance(c.get("name"),str): raise ToolError("concept needs name")
        terms=strings(c.get("any_of",[]),"any_of"); hit=[x for x in terms if x.casefold() in folded]
        (found if hit else missing).append({"name":c["name"],"matched":hit})
    missing_clauses=[x for x in clauses if x.casefold() not in folded]
    return {"ok":not missing and not missing_clauses,"found_concepts":found,"missing_concepts":missing,"missing_clauses":missing_clauses,"requirements_agent_supplied":True,"semantic_truth_verified":False}
class T(unittest.TestCase):
    def test(self): self.assertTrue(check({"text":"Action today","required_concepts":[{"name":"action","any_of":["action"]}],"required_clauses":["today"]})["ok"])
def main():
    p=Parser(); p.add_argument("command",choices=("check","selftest")); p.add_argument("--input"); a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    emit(check(read_json(a.input))); return 0
if __name__=="__main__": raise SystemExit(run(main))
