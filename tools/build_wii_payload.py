"""Wii-specific immutable glyph descriptors and guarded translation injection."""
from port_common import *
from prepare_output_probe import PPC,pack_i4,regnum
from translation_tokens import translated_tokens
from PIL import Image,ImageDraw,ImageFont
from collections import defaultdict
from unicorn import Uc,UC_ARCH_PPC,UC_MODE_PPC32,UC_MODE_BIG_ENDIAN
from unicorn import ppc_const as reg
import shutil
BASE=0x805ba000
TABLE=BASE+0x1000
BITMAPS=TABLE+0x40000
HEADER=BASE+0x300
HOOK=0x802b3f24
R13=0x805a88e0
R2=0x805aa900
SYMBOLS='…「」★☆♪①②③④⑤⑥⑦⑧⑨⑩○△□→※∞×'
THIN_SPACE=' '

def symbol_glyphs(font):
 # Digits, Latin and symbols otherwise fall back to the ROM font, and some paths widen
 # ASCII to full-width first, so both codes share one Gmarket glyph. Digits get one
 # fixed (centred) width so counters do not jitter; the rest keep Gmarket's own width.
 digit=max(round(font.getlength(d)) for d in '0123456789')+1;out=[]
 for o in range(0x21,0x7f):
  c=chr(o)
  if c in '\\~':continue
  for ch in (c,chr(o+0xfee0)):
   try:code=int.from_bytes(ch.encode('cp932'),'big')
   except UnicodeError:continue
   w=round(font.getlength(c))
   out.append(dict(character=ch,code=code,draw=c,advance=digit if c.isdigit() else w+1,dx=(digit-1-w)//2 if c.isdigit() else 0))
 for ch in SYMBOLS:out.append(dict(character=ch,code=int.from_bytes(ch.encode('cp932'),'big'),draw=ch,advance=round(font.getlength(ch))+1,dx=0))
 for m in out:
  # Keep descenders (g j p q y) inside the 24px cell instead of cutting their tails.
  x0,_,x1,y1=font.getbbox(m['draw'],anchor='ls');m['dx']-=min(0,m['dx']+x0);m['dy']=min(0,24-(18+y1))
  assert m['dx']+x1<=24
 return out

def catalog():
 # Supplemental translations/overrides live beside the hashed catalog; apply them only if
 # the catalog still holds exactly the text each record was written against.
 rows=read(ROOT/'translation/text_catalog.json')
 extra={a['id']:a for a in read(ROOT/'translation/text_additions_v07.json')['records']}
 for r in rows:
  a=extra.pop(r['id'],None)
  if a:assert r['source']==a['source'] and r['translation']==a['translation_before'],r['id'];r['translation']=a['translation']
 assert not extra,list(extra)
 return rows

def csv_fields(text):
 # home*.csv: tab-separated, quoted fields may span lines. Returns per-record (start,end) spans.
 recs=[[]];start=0;quoted=False
 for i,ch in enumerate(text):
  if ch=='"':quoted=not quoted
  elif not quoted and ch in '\t\n':
   recs[-1].append((start,i if ch=='\t' or i==0 or text[i-1]!='\r' else i-1));start=i+1
   if ch=='\n':recs.append([])
 if start<len(text):recs[-1].append((start,len(text)))
 return [r for r in recs if r]

def korean_home(files):
 # The disc already carries Nintendo's own Korean HOME menu (homeBtn_KOR.arc, KOR column 9).
 # A Japanese console always loads homeBtn.arc and column 0, so point both at the Korean data.
 hbm=ORIGINAL/'files/hbm';out=[]
 jp,kor=(hbm/'homeBtn.arc').read_bytes(),(hbm/'homeBtn_KOR.arc').read_bytes()
 (files/'hbm/homeBtn.arc').write_bytes(kor);out.append(dict(file='hbm/homeBtn.arc',old_sha256=sha(jp),new_sha256=sha(kor),source='hbm/homeBtn_KOR.arc'))
 for name in ['home.csv','home_nosave.csv']:
  raw=(hbm/name).read_bytes();assert raw[:2]==b'\xfe\xff';text=raw[2:].decode('utf-16-be');recs=csv_fields(text)
  assert all(len(r)==10 for r in recs) and len(recs)==4
  new=text
  for r in reversed(recs):(a,b),(c,e)=r[0],r[9];new=new[:a]+text[c:e]+new[b:]
  check=csv_fields(new)
  assert all(new[slice(*n[i])]==text[slice(*o[i])] for o,n in zip(recs,check) for i in range(1,10))
  assert all(new[slice(*n[0])]==text[slice(*o[9])] for o,n in zip(recs,check))
  data=b'\xfe\xff'+new.encode('utf-16-be');(files/'hbm'/name).write_bytes(data)
  out.append(dict(file='hbm/'+name,old_sha256=sha(raw),new_sha256=sha(data),japanese_column_from='column 9 (KOR)'))
 return out

def enc(text,mapping):
 return b''.join(mapping[c].to_bytes(2,'big') if c in mapping and mapping[c]>255 else bytes([mapping[c]]) if c in mapping else c.encode('cp932') for c in text)
def body(r,m):return b''.join(enc(t['source'],m) if t['kind']=='text' else bytes.fromhex(t['hex']) for t in translated_tokens(r))
def branch(a,b):
 s=PPC(a);s.branch(b);return s.finish()

def glyph_hook():
 s=PPC(BASE)
 # The original path stores the 0x43300000 integer-to-double bias at
 # 0x802b3f28/0x802b3f30. Our early branch bypasses those stores, but
 # the common UV calculation at 0x802b4154 still consumes both slots.
 # r7 was initialized by the unmodified prologue before this hook.
 s.d(36,7,1,0x60);s.d(36,7,1,0x68)
 s.d(34,8,29,0);s.d(10,0,8,128);s.bc(0x41800000,'single')
 s.emit(0x5508402e);s.d(34,9,29,1);s.emit(0x7d084b78)
 s.label('single');s.emit(21<<26|8<<21|8<<16|2<<11|29<<1)
 s.load(9,TABLE);s.emit(31<<26|10<<21|9<<16|8<<11|23<<1)
 s.d(11,0,10,0);s.bc(0x41820000,'fallback')
 s.emit(21<<26|10<<21|4<<16|26<<1);s.d(28,10,0,31);s.d(36,0,1,0xc)
 s.d(14,0,0,0);s.d(36,0,1,0x10);s.d(36,0,1,0x14)
 s.emit(0x7fc3f378);s.load(5,HEADER);s.branch(0x802b3d70,True);s.branch(0x802b4144)
 s.label('fallback');s.d(32,0,13,-0x6048);s.branch(HOOK+4)
 return s.finish()

def cpu(dol):
 u=Uc(UC_ARCH_PPC,UC_MODE_PPC32|UC_MODE_BIG_ENDIAN);u.mem_map(0x80000000,0x2000000)
 for s in sections(dol):u.mem_write(s['address'],bytes(dol[s['offset']:s['offset']+s['size']]))
 u.reg_write(reg.UC_PPC_REG_MSR,0x2000);u.reg_write(regnum(1),0x817f0000);u.reg_write(regnum(13),R13);u.reg_write(regnum(2),R2)
 return u

def verify_font(dol,mapping,blob,entries,end):
 u=cpu(dol);obj=0x81000000;string=0x81001000;width=0x81002000
 for i,m in enumerate(entries):
  code=m['code'];u.mem_write(string,code.to_bytes(2,'big')+b'\0' if code>255 else bytes([code,0]))
  for r,v in {1:0x817f0000,3:obj,4:string,5:0,6:width}.items():u.reg_write(regnum(r),v)
  u.reg_write(reg.UC_PPC_REG_LR,0x81ffff00);u.emu_start(0x802b3efc,0x802b4144,count=5000)
  assert u.reg_read(reg.UC_PPC_REG_PC)==0x802b4144
  sp=u.reg_read(regnum(1));assert int.from_bytes(u.mem_read(sp+0xc,4),'big')==m['advance']
  assert bytes(u.mem_read(sp+0x10,8))==bytes(8)
  ptr=int.from_bytes(u.mem_read(obj+0x10,4),'big');assert ptr==BITMAPS+i*288
  assert bytes(u.mem_read(ptr,288))==blob[i*288:i*288+288]
  assert bytes(u.mem_read(obj+8,8))==bytes.fromhex('0018001800000000')
 # Fallback takes the exact displaced instruction without altering arguments.
 u=cpu(dol);u.mem_write(R13-0x6048,struct.pack('>I',0x81234560))
 fallback=[c for c in ['\\','A',' ','は','亜'] if c not in mapping]
 for c in fallback:
  u.mem_write(string,c.encode('cp932')+b'\0');u.reg_write(regnum(29),string)
  u.emu_start(HOOK,HOOK+4,count=100)
  assert u.reg_read(regnum(0))==0x81234560
 for requested in [BASE-32,BASE,end-32,end,end+32]:
  for fun in [0x80181788,0x80181798]:
   u.reg_write(regnum(3),requested);u.reg_write(reg.UC_PPC_REG_LR,0x81ffff00)
   u.emu_start(fun,0x81ffff00,count=100)
   assert int.from_bytes(u.mem_read(R13-0x7500,4),'big')==max(end,requested)
 return dict(glyph_descriptors=len(entries),fallback_cases=len(fallback),arena_cases=10,actual_descriptor_constructor_executed=True,gpu_verified=False)

def main():
 rows=catalog();selected=[r for r in rows if r['translation'] is not None]
 required=set(c for r in selected for t in translated_tokens(r) if t['kind']=='text' for c in t['source'])
 oldplan=read(GC/'translation/full_font_plan.json')['mapping'];extras=read(GC/'metadata/v03_corrections_verification.json')['font_additions']
 entries=[dict(m) for m in oldplan+extras];used={m['code'] for m in entries};mapping={m['character']:m['code'] for m in entries}
 codes=iter(c for hi in range(0xf0,0xfa) for lo in range(0x40,0xfd) if lo!=0x7f for c in [hi*256+lo] if c not in used)
 for c in sorted(required):
  try:c.encode('cp932')
  except UnicodeError:
   if c not in mapping:
    code=next(codes);mapping[c]=code
    # U+2009: a blank two-byte narrow space for the ChibiCom ticker, which only takes
    # two-byte characters (the full-width space leaves very wide gaps there).
    entries.append(dict(character=c,code=code,advance=7,draw=' ') if c==THIN_SPACE else dict(character=c,code=code,advance=20))
 font=ImageFont.truetype(str(ROOT/'work/references/gmarket/GmarketSansBold.otf'),20)
 for m in symbol_glyphs(font):
  assert m['character'] not in mapping and m['code'] not in {e['code'] for e in entries} and m['advance']<32
  mapping[m['character']]=m['code'];entries.append(m)
 # Reuse the exact GC v05 font pixels (incl. v03 tilde), kept locally because the GC
 # project no longer keeps its v05 ISO. Taken from the verified Wii v08 DOL.
 gcglyphs=(ROOT/'work/font/gc_v05_glyphs.i4').read_bytes();preserved=len(oldplan)+len(extras)
 assert sha(gcglyphs)=='568d52ae7fdc6ff352bd915545087ad6a7cee8aa51867a38b41fb44cd3180cc9' and len(gcglyphs)==preserved*288
 blob=bytearray()
 for i,m in enumerate(entries):
  if i<preserved:raw=gcglyphs[i*288:i*288+288]
  else:
   im=Image.new('L',(24,24));ImageDraw.Draw(im).text((m.get('dx',0),18+m.get('dy',0)),m.get('draw',m['character']),font=font,fill=255,anchor='ls');raw=pack_i4(im)
  assert len(raw)==288;blob.extend(raw)
 save(ROOT/'translation/wii_font_plan.json',dict(mapping=entries,base=BASE,bitmaps=BITMAPS,font='Gmarket Sans Bold 20px',gc_pixels_preserved=len(oldplan)+len(extras)))
 # Stage the original WIT extraction so partition metadata remains usable.
 stage=ROOT/'work/patched';shutil.copytree(ROOT/'work/wit-original',stage,dirs_exist_ok=True)
 files=stage/'files'
 if not files.exists():stage=stage/'DATA';files=stage/'files'
 assert files.exists()
 home=korean_home(files)
 groups=defaultdict(list)
 for r in selected:
  if r['kind']=='script_message_candidate':groups[r['file']].append(r)
 changes=[]
 for file,items in groups.items():
  original=(ORIGINAL/'files'/file).read_bytes();b=bytearray(original);base=struct.unpack_from('<I',b,16)[0]+24 if file=='bin/globals.bin' else 0;patches=[];prev=-1
  for r in sorted(items,key=lambda x:x['opcode_offset']):
   at=r['opcode_offset'];assert prev<=at;prev=r['end'];raw=body(r,mapping)
   assert original[at+5:r['end']]==b''.join(bytes.fromhex(t['hex']) for t in r['tokens'])
   start=len(b);finish=start+5+len(raw);b.extend(bytes([r['opcode']])+struct.pack('<I',finish-base)+raw+b'\x03'+struct.pack('<I',r['end']-base))
   patches.append((at,bytes(b[at:at+5])));b[at:at+5]=b'\x03'+struct.pack('<I',start-base)
   assert struct.unpack_from('<I',b,at+1)[0]+base==start and b[start+5:finish]==raw
  if base:patches.append((20,bytes(b[20:24])));struct.pack_into('<I',b,20,len(b)-base)
  restore=bytearray(b[:len(original)])
  for at,raw in patches:restore[at:at+len(raw)]=raw
  assert restore==original
  (files/file).write_bytes(b);changes.append(dict(file=file,messages=len(items),old_size=len(original),new_size=len(b)))
 file='bin/globals.bin';original=(ORIGINAL/'files'/file).read_bytes();b=bytearray((files/file).read_bytes());h=struct.unpack_from('<6I',original);base=24+h[0];meta=bytearray(original[base:base+h[1]])
 for r in selected:
  if r['kind']!='metadata_string':continue
  raw=body(r,mapping);ptr=r['pointer_offset']-base;assert base+struct.unpack_from('<I',meta,ptr)[0]==r['offset'];struct.pack_into('<I',meta,ptr,len(meta));meta.extend(raw)
 start=align(len(b));b.extend(bytes(start-len(b)));b.extend(meta);struct.pack_into('<II',b,0,start-24,len(meta));(files/file).write_bytes(b)
 dol=bytearray((ORIGINAL/'sys/main.dol').read_bytes());payload=bytearray(BITMAPS-BASE);hook=glyph_hook();payload[:len(hook)]=hook
 header=bytearray(48)
 for at in [0x10,0x12,0x1e,0x20]:struct.pack_into('>H',header,at,24)
 payload[HEADER-BASE:HEADER-BASE+48]=header
 for i,m in enumerate(entries):struct.pack_into('>I',payload,TABLE-BASE+m['code']*4,(BITMAPS+i*288)|m['advance'])
 payload.extend(blob);ui=[]
 for r in selected:
  if r['kind']!='dol_rodata_string_candidate':continue
  payload.extend(bytes((-len(payload))%4));a=BASE+len(payload);raw=body(r,mapping);payload.extend(raw)
  for off in r['references']:
   assert struct.unpack_from('>I',dol,off)[0]==address(dol,r['offset']);struct.pack_into('>I',dol,off,a)
  ui.append(dict(id=r['id'],address=a,bytes=len(raw)))
 end=align(BASE+len(payload),4096);payload.extend(bytes(end-BASE-len(payload)))
 clamp=PPC(BASE+0x200);clamp.load(11,end);clamp.emit(0x7c035840);clamp.bc(0x40800000,'orig');clamp.d(36,11,13,-0x7500);clamp.emit(0x4e800020);clamp.label('orig');clamp.d(36,3,13,-0x7500);clamp.emit(0x4e800020)
 cl=clamp.finish();payload[0x200:0x200+len(cl)]=cl
 assert dol[offset(dol,HOOK):offset(dol,HOOK)+4]==bytes.fromhex('800d9fb8')
 dol[offset(dol,HOOK):offset(dol,HOOK)+4]=branch(HOOK,BASE)
 for a in [0x80181788,0x80181798]:
  o=offset(dol,a);assert dol[o:o+4]==bytes.fromhex('906d8b00');dol[o:o+4]=branch(a,BASE+0x200)
 assert all(s['address']+s['size']<=BASE or s['address']>=end for s in sections(dol))
 bss,length=struct.unpack_from('>II',dol,0xd8);assert bss+length<BASE
 assert all(struct.unpack_from('>I',dol,o)[0]==0 for o in [8,0x50,0x98])
 off=align(len(dol));dol.extend(bytes(off-len(dol)));struct.pack_into('>I',dol,8,off);struct.pack_into('>I',dol,0x50,BASE);struct.pack_into('>I',dol,0x98,len(payload));dol.extend(payload)
 checks=verify_font(dol,mapping,blob,entries,end)
 (stage/'sys/main.dol').write_bytes(dol)
 save(ROOT/'metadata/payload_verification.json',dict(texts=len(selected),by_kind=dict(__import__('collections').Counter(r['kind'] for r in selected)),glyphs=len(entries),font=checks,reserved_start=hex(BASE),reserved_end=hex(end),dol_sha256=sha(dol),files=changes,ui=ui,home=home,runtime_verified=False))
 print('PASS',len(selected),'texts',len(entries),'glyphs',checks,'DOL',len(dol),hex(end))
if __name__=='__main__':main()
