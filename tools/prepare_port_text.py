"""Keep Wii message controls and relocate only independently matched translations."""
from port_common import *
from analyze_stage1 import parse_msg
from translation_tokens import translated_tokens,bounds,template
from collections import defaultdict,Counter
import re

def scan():
 rows=[]
 for path in sorted((ORIGINAL/'files/bin').glob('*.bin')):
  original=path.read_bytes();raw=original;base=0
  if path.name=='globals.bin':
   h=struct.unpack_from('<6I',raw);base=h[4]+24;raw=raw[base:base+h[5]]
  for i,c in enumerate(raw[:-6]):
   if c not in (0x23,0x2b):continue
   end=struct.unpack_from('<I',raw,i+1)[0]
   if not i+6<=end<=min(len(raw),i+4096) or raw[end-1]!=0:continue
   try:source,tokens,tags=parse_msg(raw[i+5:end],'jp')
   except (ValueError,UnicodeError):continue
   rows.append(dict(id=f'bin/{path.name}@{base+i+5:08x}',file='bin/'+path.name,kind='script_message_candidate',offset=base+i+5,opcode_offset=base+i,opcode=c,end=base+end,source=source,tokens=tokens,translation=None))
 b=(ORIGINAL/'files/bin/globals.bin').read_bytes();h=struct.unpack_from('<6I',b);base=24+h[0];m=b[base:base+h[1]];head=struct.unpack_from('<21I',m)
 tables=[('item',10,159,20,2),('actor',11,64,4,1),('equipment',12,9,12,2),('suit',13,9,4,1),('stage',14,30,8,2),('leticker',18,20,12,2),('sticker',19,24,12,2),('stat',20,13,8,2)]
 for kind,hi,count,stride,fields in tables:
  table=head[hi];assert struct.unpack_from('<I',m,table)[0]==table+count*stride,(kind,hex(table))
  for i in range(count):
   for j in range(fields):
    ptr=table+i*stride+j*4;at=struct.unpack_from('<I',m,ptr)[0];end=m.index(0,at)+1
    source,tokens,_=parse_msg(m[at:end],'jp')
    rows.append(dict(id=f'globals:{kind}.{i}.{j}',label=f'{kind}.{i}.{j}',file='bin/globals.bin',kind='metadata_string',offset=base+at,end=base+end,pointer_offset=base+ptr,source=source,tokens=tokens,translation=None))
 return rows

def transfer(old,new):
 # Same visible source; every visible control must have the same kind and order.
 lo,hi=bounds(old);nl,nh=bounds(new)
 oc=[(i,t['kind']) for i,t in enumerate(old['tokens']) if lo<=i<=hi and t['kind']!='text']
 nc=[(i,t['kind']) for i,t in enumerate(new['tokens']) if nl<=i<=nh and t['kind']!='text']
 if [k for _,k in oc]!=[k for _,k in nc]:return None
 index={a:b for (a,_),(b,_) in zip(oc,nc)}
 target=re.sub(r'<(\d+)>',lambda m:f'<{index[int(m[1])]}>',old['translation'])
 test=dict(new,translation=target);translated_tokens(test)
 return target

def main():
 old=read(GC/'translation/text_catalog.json');scope=read(GC/'metadata/build_scope_proposal.json')['record_ids_by_bucket']
 allowed=set(sum([scope[k] for k in ['script_test_candidate','metadata_test_candidate','ui_test_candidate_runtime_unverified']],[]))
 source=defaultdict(list)
 for r in old:
  if r['id'] in allowed and r.get('translation') is not None:source[(r['kind'],r['file'],r['source'])].append(r)
 rows=scan()
 for r in rows:
  options=source[(r['kind'],r['file'],r['source'])]
  matches=[]
  for o in options:
   try:t=transfer(o,r)
   except (ValueError,KeyError,StopIteration):continue
   if t is not None:matches.append((t,o['id']))
  if len(set(t for t,_ in matches))==1:
   r['translation'],r['gc_id']=matches[0];r['origin']='gc_v05_source_and_control_match'
  elif matches:r['hold_reason']='same_source_different_translations'
 b=(ORIGINAL/'sys/main.dol').read_bytes();ui=defaultdict(set)
 for o in old:
  if o['kind']=='dol_rodata_string_candidate' and o['id'] in allowed:ui[o['source']].add(o['translation'])
 for o in read(GC/'translation/ui_corrections_v03.json')['records']:ui[o['source']].add(o['translation'])
 pointer_index=defaultdict(list)
 for sec in sections(b):
  if sec['index']>=7:
   for off in range(sec['offset'],sec['offset']+sec['size']-3,4):pointer_index[struct.unpack_from('>I',b,off)[0]].append(off)
 for s in sections(b):
  if s['index']<7:continue
  a=s['offset'];end=a+s['size']
  for m in re.finditer(rb'[^\x00]{2,}\x00',b[a:end]):
   at=a+m.start();raw=m[0][:-1]
   try:text=raw.decode('cp932')
   except UnicodeError:continue
   if not re.search('[ぁ-ヿ一-鿿]',text) or any(ord(c)<32 and c not in '\n\t' for c in text):continue
   addr=address(b,at);refs=pointer_index[addr]
   if not refs:continue
   trans=next(iter(ui[text])) if len(ui[text])==1 else None
   rows.append(dict(id=f'main.dol@{at:08x}',file='main.dol',kind='dol_rodata_string_candidate',offset=at,end=at+len(raw)+1,source=text,tokens=[dict(kind='text',source=text,hex=raw.hex()),dict(kind='end',hex='00')],references=refs,translation=trans,origin='gc_v05_ui_source_match' if trans else 'wii_ui_pending'))
 save(ROOT/'translation/text_catalog.json',rows)
 pending=[dict(id=r['id'],kind=r['kind'],source=r['source'],template=template(r) if any(t['kind'] in ('text','format','icon') for t in r['tokens']) else '') for r in rows if r['translation'] is None and re.search('[ぁ-ヿ一-鿿]',r['source'])]
 save(ROOT/'work/pending-text.json',pending)
 print(Counter((r['kind'],r['translation'] is not None) for r in rows));print('Japanese pending',len(pending))
if __name__=='__main__':main()
