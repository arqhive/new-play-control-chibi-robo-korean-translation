from pathlib import Path
import json,struct,hashlib
ROOT=Path(__file__).resolve().parents[1]
GC=ROOT.with_name('[GC] 치비로보')
ORIGINAL=ROOT/'work/original/DATA'
def read(p):return json.loads(Path(p).read_text('utf-8'))
def save(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def align(x,n=32):return (x+n-1)//n*n
def sections(b):
 return [dict(index=i,offset=struct.unpack_from('>I',b,i*4)[0],address=struct.unpack_from('>I',b,0x48+i*4)[0],size=struct.unpack_from('>I',b,0x90+i*4)[0]) for i in range(18) if struct.unpack_from('>I',b,0x90+i*4)[0]]
def offset(b,a):
 s=next(s for s in sections(b) if s['address']<=a<s['address']+s['size']);return s['offset']+a-s['address']
def address(b,o):
 s=next(s for s in sections(b) if s['offset']<=o<s['offset']+s['size']);return s['address']+o-s['offset']
