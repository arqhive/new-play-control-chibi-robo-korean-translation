from port_common import *
from finish_survey import u8,unwrap
from port_graphics import rgba8
from verify_graphics_encoding import encode
from decode_gx import decode,size
from PIL import Image
import numpy as np
from collections import defaultdict,deque

def replace_u8(raw,replacements):
 if not replacements:return raw
 b=bytearray(raw);at=b.index(b'U\xaa8-');root=at+struct.unpack_from('>I',b,at+4)[0];n=struct.unpack_from('>I',b,root+8)[0];strings=root+n*12;stack=[];seen=set()
 for i in range(1,n):
  while stack and i>=stack[-1][0]:stack.pop()
  node=root+i*12;typ,o,z=struct.unpack_from('>III',b,node);s=strings+(typ&0xffffff);name=b[s:b.index(0,s)].decode();path='/'.join([p for _,p in stack]+[name])
  if typ>>24:stack.append((z,name));continue
  if path not in replacements:continue
  data=replacements[path];seen.add(path)
  if len(data)==z:b[at+o:at+o+z]=data
  else:
   new=align(len(b));b.extend(bytes(new-len(b)));b.extend(data);struct.pack_into('>II',b,node+4,new-at,len(data))
 assert seen==set(replacements)
 before=dict(u8(raw));after=dict(u8(b));assert before.keys()==after.keys()
 for k in before:assert after[k]==replacements.get(k,before[k]),k
 return bytes(b)

def compress_lz10(b):
 out=bytearray(b'LZ77\x10'+len(b).to_bytes(3,'little'));history=defaultdict(deque);p=0
 while p<len(b):
  flagpos=len(out);out.append(0);flags=0
  for bit in range(7,-1,-1):
   if p>=len(b):break
   start=p;best=0;distance=0;key=b[p:p+3];q=history[key]
   while q and q[0]<p-4096:q.popleft()
   for prev in reversed(q):
    length=0
    while length<18 and p+length<len(b) and b[prev+length]==b[p+length]:length+=1
    if length>best:best=length;distance=p-prev
    if best==18:break
   if best>=3:
    flags|=1<<bit;v=((best-3)<<12)|(distance-1);out.extend(v.to_bytes(2,'big'));p+=best
   else:out.append(b[p]);p+=1
   for a in range(start,p):history[b[a:a+3]].append(a)
  out[flagpos]=flags
 return bytes(out)

def imd5(original,raw):
 assert original[:4]==b'IMD5';payload=compress_lz10(raw);header=bytearray(original[:32]);struct.pack_into('>I',header,4,len(payload));header[16:32]=hashlib.md5(payload).digest();out=bytes(header)+payload;assert unwrap(out)==raw;return out

def patch_tpl(raw,image,entry=0,rgba=False):
 b=bytearray(raw);magic,count,table=struct.unpack_from('>III',b);assert magic==0x20af30 and entry<count
 header,palette=struct.unpack_from('>II',b,table+8*entry);h,w,fmt,at=struct.unpack_from('>HHII',b,header);assert image.size==(w,h) and not palette
 old=decode(bytes(b[at:at+size(w,h,fmt)]),w,h,fmt)
 if rgba:
  data=rgba8(image);fmt=6;at=align(len(b));b.extend(bytes(at-len(b)));b.extend(data);struct.pack_into('>II',b,header+4,fmt,at)
 else:
  n=size(w,h,fmt);data,_,_=encode(bytes(b[at:at+n]),image,fmt);b[at:at+n]=data
 final=decode(data,w,h,fmt);a=np.array(old);c=np.array(image);d=np.array(final);outside=np.all(a==c,2);assert np.array_equal(a[outside],d[outside])
 if rgba:assert np.array_equal(c,d)
 return bytes(b),final,dict(format=fmt,dimensions=[w,h],outside_edit_mask_changed_pixels=0,png_exact=rgba)

def main():
 rows=read(ROOT/'metadata/remaining_image_drafts.json')['images'];cat={r['id']:r for r in read(ROOT/'metadata/graphics_catalog.json')};stage=ROOT/'work/patched/files';report=[];containers={};nested=defaultdict(dict)
 out=ROOT/'work/remaining-images/encoded';out.mkdir(exist_ok=True)
 for r in rows:
  p=ROOT/r['candidate_path'];assert sha(p.read_bytes())==r['candidate_sha256'];im=Image.open(p).convert('RGBA')
  if r['kind']=='tpl':
   t=cat[r['target']];file=t['file']
   # Reuse the current GC-port stage; retain all earlier misc.tpl replacements.
   if file not in containers:containers[file]=(stage/file).read_bytes()
   b,decoded,info=patch_tpl(containers[file],im,int(r['target'].split('-')[-1]),r['key'].startswith('controller'))
   containers[file]=b
  else:
   container,inner=r['target'].split('/arc/',1);inner='arc/'+inner
   nested[container][inner]=(r,im);continue
  decoded.save(out/(r['key']+'.png'));report.append(dict(**r,encoding=info))
 original=(ORIGINAL/'files/opening.bnr').read_bytes();outer=dict(u8(original));outerreplace={};allmodified=set()
 assert replace_u8(original,{})==original
 for name,repls in nested.items():
  old=unwrap(outer[name]);leaves=dict(u8(old));changed={}
  assert replace_u8(old,{})==old
  for leaf,(r,im) in repls.items():
   encoded,decoded,info=patch_tpl(leaves[leaf],im);changed[leaf]=encoded;allmodified.add(name+'/'+leaf);decoded.save(out/(r['key']+'.png'));report.append(dict(**r,encoding=info))
  changedraw=replace_u8(old,changed);assert len(changedraw)==len(old)
  outerreplace[name]=imd5(outer[name],changedraw)
 banner=replace_u8(original,outerreplace)
 assert banner[:0x600]==original[:0x600]
 header=bytearray(banner[:0x600]);digest=header[-16:];header[-16:]=bytes(16);assert hashlib.md5(header).digest()==digest
 for name,data in dict(u8(banner)).items():
  assert data[:4]==b'IMD5';assert struct.unpack_from('>I',data,4)[0]==len(data)-32;assert hashlib.md5(data[32:]).digest()==data[16:32]
  if name not in outerreplace:assert data==outer[name]
 containers['opening.bnr']=banner
 for file,b in containers.items():(stage/file).write_bytes(b)
 save(ROOT/'metadata/remaining_image_injection.json',dict(images=report,containers=[dict(file=f,size=len(b),sha256=sha(b)) for f,b in containers.items()],banner_unmodified_resources_preserved=True,imet_unchanged_md5_verified=True,imd5_verified=True,compression='LZ77 type 0x10 preserved',runtime_verified=False))
 print('PASS',len(report),'images;',len(containers),'containers; banner archive/checksums verified')
if __name__=='__main__':main()
