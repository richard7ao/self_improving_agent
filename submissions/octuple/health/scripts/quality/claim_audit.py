#!/usr/bin/env python3
from __future__ import annotations
import re, unittest
from toolkit_common import Parser, emit, read_text, run
PATTERNS={"absolute":r"\b(always|never|impossible|guaranteed)\b","certainty":r"\b(definitely|certainly|proves?|confirmed)\b","safety_absolute":r"\b(completely safe|no risk|cannot harm)\b"}
def check(text):
    warnings=[]
    for kind,pat in PATTERNS.items():
        for m in re.finditer(pat,text,re.I): warnings.append({"kind":kind,"phrase":m.group(0),"start":m.start()})
    return {"ok":True,"warning_count":len(warnings),"warnings":warnings,"semantic_certification":False,"instruction":"Review flags in context; justified wording may remain."}
class T(unittest.TestCase):
    def test_flags(self): self.assertEqual(check("This is definitely safe.")["warning_count"],1)
    def test_never_certifies(self): self.assertFalse(check("Maybe.")["semantic_certification"])
def main():
    p=Parser(); p.add_argument("command",choices=("check","selftest")); p.add_argument("--input"); a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    emit(check(read_text(a.input))); return 0
if __name__=="__main__": raise SystemExit(run(main))
