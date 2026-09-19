#!/usr/bin/env python3
from __future__ import annotations
import re, unittest
from toolkit_common import Parser, ToolError, emit, read_json, run
UNITS=("words","sentences","questions","paragraphs","bullets")
def counts(t):
    s=t.strip(); return {"words":len(re.findall(r"\b[^\W_]+(?:['’-][^\W_]+)*\b",t)),"sentences":len(re.findall(r"[^.!?]+(?:[.!?]+(?=\s|$)|$)",s)) if s else 0,"questions":t.count("?"),"paragraphs":len(re.findall(r"\S(?:.*?\S)?(?=\n\s*\n|\Z)",s,re.S)) if s else 0,"bullets":sum(bool(re.match(r"^\s*(?:[-+*]|\d+[.)])\s+\S",x)) for x in t.splitlines())}
def check(v):
    if not isinstance(v,dict) or not isinstance(v.get("text"),str): raise ToolError("text must be a string")
    t=v["text"]; c=counts(t); issues=[]; folded=t.casefold()
    for x in v.get("required",[]):
        if x.casefold() not in folded: issues.append(f"missing required: {x}")
    for x in v.get("forbidden",[]):
        if x.casefold() in folded: issues.append(f"contains forbidden: {x}")
    if "prefix" in v and not t.startswith(v["prefix"]): issues.append("prefix mismatch")
    if "suffix" in v and not t.endswith(v["suffix"]): issues.append("suffix mismatch")
    for bound,op,word in (("min",lambda a,b:a<b,"below"),("max",lambda a,b:a>b,"above"),("exact",lambda a,b:a!=b,"not equal")):
        for unit,target in v.get(bound,{}).items():
            if unit not in UNITS or not isinstance(target,int) or target<0: raise ToolError("invalid count bound")
            if op(c[unit],target): issues.append(f"{unit} {word} {target}")
    sections=v.get("sections",[]); positions=[]
    for name in sections:
        if not isinstance(name,str) or not name: raise ToolError("section names must be strings")
        ms=list(re.finditer(rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(name)}\s*:?[ \t]*(.*)$",t))
        if len(ms)!=1: issues.append(f"section {name} occurrences: {len(ms)}"); continue
        positions.append(ms[0].start()); starts=sorted(m.start() for n in sections for m in re.finditer(rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(n)}\s*:?[ \t]*(.*)$",t))
        end=next((x for x in starts if x>ms[0].start()),len(t)); body=(ms[0].group(1)+t[ms[0].end():end]).strip()
        if not body: issues.append(f"empty section: {name}")
    if positions!=sorted(positions): issues.append("section order mismatch")
    return {"ok":not issues,"counts":c,"issues":issues,"semantic_truth_verified":False}
class T(unittest.TestCase):
    def test_pass(self): self.assertTrue(check({"text":"## A\nOne.\n\n## B\n- Two?","exact":{"paragraphs":2,"bullets":1},"sections":["A","B"]})["ok"])
    def test_fail(self): self.assertFalse(check({"text":"x","required":["y"]})["ok"])
def main():
    p=Parser(); p.add_argument("command",choices=("check","selftest")); p.add_argument("--input"); a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    emit(check(read_json(a.input))); return 0
if __name__=="__main__": raise SystemExit(run(main))
