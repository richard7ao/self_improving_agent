#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, tempfile, unicodedata, unittest
from pathlib import Path
from toolkit_common import Parser, ToolError, atomic_write, canonical, emit, read_bytes, read_text, run
from response_delivery import deliver as deliver_bytes
BASE=Path("/logs/agent/questions"); OUTPUT=Path("/logs/agent/response.txt"); ID=re.compile(r"^[0-9a-f]{16}$"); EDITABLE=("draft","final")
def identity(text):
    norm="\n".join(x.rstrip() for x in unicodedata.normalize("NFC",text.replace("\r\n","\n").replace("\r","\n")).split("\n")).strip()
    if not norm: raise ToolError("question is empty")
    digest=hashlib.sha256(norm.encode()).hexdigest(); return norm,digest[:16],digest
def safe_base(base):
    if not base.is_absolute() or base.is_symlink(): raise ToolError("unsafe base")
    return base.resolve(strict=False)
def folder(base,qid,exists=True):
    base=safe_base(base)
    if not ID.fullmatch(qid): raise ToolError("invalid question ID")
    p=base/qid
    if p.is_symlink() or (exists and not p.is_dir()): raise ToolError("workspace missing or unsafe")
    return p
def init(base,text):
    norm,qid,digest=identity(text); base=safe_base(base); base.mkdir(parents=True,exist_ok=True); p=folder(base,qid,False); expected=(norm+"\n").encode()
    if p.exists():
        if not p.is_dir() or (p/"question.txt").read_bytes()!=expected: raise ToolError("collision or unrelated work")
        return p,False
    p.mkdir();
    for name,data in {"question.txt":expected,"draft.txt":b"","final.txt":b"","manifest.json":canonical({"archived":False,"delivered":False,"final_sha256":None,"question_id":qid,"question_sha256":digest,"schema_version":1})}.items(): atomic_write(p/name,data)
    return p,True
def save(p,name,data):
    if name not in EDITABLE: raise ToolError("artifact is not editable")
    try: data.decode("utf-8")
    except UnicodeError as e: raise ToolError("artifact must be UTF-8") from e
    return atomic_write(p/f"{name}.txt",data)
def deliver(p,output):
    final=(p/"final.txt").read_bytes(); result=deliver_bytes(final,output) # Deliver before archive.
    archive=atomic_write(p/"delivered.txt",final)
    if archive.read_bytes()!=final: raise ToolError("archive mismatch")
    manifest=json.loads((p/"manifest.json").read_text()); manifest.update({"archived":True,"delivered":True,"delivery_path":result["output"],"final_sha256":result["sha256"]}); atomic_write(p/"manifest.json",canonical(manifest))
    return {**result,"archived":True,"workspace":str(p)}
class T(unittest.TestCase):
    def test_stable_and_preserve(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/"q"; p,c=init(b,"Café\r\nQ "); self.assertTrue(c); save(p,"draft",b"work"); p2,c2=init(b,"Cafe\u0301\nQ"); self.assertFalse(c2); self.assertEqual((p2/"draft.txt").read_bytes(),b"work")
    def test_delivery_first_archive(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d)/"q"; p,_=init(b,"Q"); save(p,"final","answer".encode()); out=Path(d)/"response"; r=deliver(p,out); self.assertTrue(r["archived"]); self.assertEqual(out.read_bytes(),(p/"delivered.txt").read_bytes())
    def test_empty_not_archived(self):
        with tempfile.TemporaryDirectory() as d:
            p,_=init(Path(d)/"q","Q")
            with self.assertRaises(ToolError): deliver(p,Path(d)/"out")
            self.assertFalse((p/"delivered.txt").exists())
def main():
    p=Parser(); p.add_argument("--base",type=Path,default=BASE); sub=p.add_subparsers(dest="command",required=True)
    i=sub.add_parser("init"); i.add_argument("--question-file")
    for command in ("path","show","deliver"):
        x=sub.add_parser(command); x.add_argument("--id",required=True)
        if command=="show": x.add_argument("--artifact",choices=("question","draft","final","delivered","manifest"),required=True)
        if command=="deliver": x.add_argument("--output",type=Path,default=OUTPUT)
    s=sub.add_parser("save"); s.add_argument("--id",required=True); s.add_argument("--artifact",choices=EDITABLE,required=True); s.add_argument("--file")
    sub.add_parser("selftest"); a=p.parse_args()
    if a.command=="selftest": return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(T)).wasSuccessful() else 1
    if a.command=="init":
        w,created=init(a.base,read_text(a.question_file)); emit({"ok":True,"id":w.name,"path":str(w),"created":created}); return 0
    w=folder(a.base,a.id)
    if a.command=="path": result={"ok":True,"id":a.id,"path":str(w)}
    elif a.command=="save": result={"ok":True,"artifact":a.artifact,"bytes":save(w,a.artifact,read_bytes(a.file)).stat().st_size}
    elif a.command=="show":
        path=w/(a.artifact+(".json" if a.artifact=="manifest" else ".txt")); result={"ok":True,"artifact":a.artifact,"value":json.loads(path.read_text()) if a.artifact=="manifest" else path.read_text()}
    else: result=deliver(w,a.output)
    emit(result); return 0
if __name__=="__main__": raise SystemExit(run(main))
