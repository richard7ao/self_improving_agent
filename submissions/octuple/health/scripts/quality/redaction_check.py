#!/usr/bin/env python3
from __future__ import annotations
import re, unittest
from toolkit_common import Parser, emit, read_text, run
P={"email":r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b","phone":r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)","record_identifier":r"(?i)\b(?:medical record|record number|patient id|date of birth)\s*[:#]","secret":r"(?i)\b(?:api[_ -]?key|password|secret|bearer)\s*[:=]"}
def check(t):
    warnings=[]
    for kind,p in P.items():
        for m in re.finditer(p,t): warnings.append({"kind":kind,"start":m.start(),"text":m.group(0)[:80]})
    return {"ok":True,"warning_count":len(warnings),"warnings":warnings,"deidentification_proven":False,"instruction":"Review and redact in context; patterns are incomplete and may be false positives."}
class T(unittest.TestCase):
    def test_email(self): self.assertEqual(check("contact person@example.test")["warning_count"],1)
    def test_not_proof(self): self.assertFalse(check("text")["deidentification_proven"])
def main():
    p=Parser(); p.add_argument("command",choices=("check","selftest")); p.add_argument("--input"); a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    emit(check(read_text(a.input))); return 0
if __name__=="__main__": raise SystemExit(run(main))
