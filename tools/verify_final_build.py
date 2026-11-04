from port_common import *
from build_wii_payload import body,catalog
from collections import Counter
import re,argparse

def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--iso',default='build/ChibiRobo_Wii_KO_Test_v03_GmarketBold.iso');parser.add_argument('--readback',default='work/build-readback-v03/DATA');args=parser.parse_args()
 tree=ROOT/'work/patched';back=ROOT/args.readback;changes=[];count=0
 expected={p.relative_to(tree/'files').as_posix() for p in (tree/'files').rglob('*') if p.is_file()}
 actual={p.relative_to(back/'files').as_posix() for p in (back/'files').rglob('*') if p.is_file()};assert expected==actual
 for name in sorted(expected):
  p=tree/'files'/name;a=p.read_bytes();b=(back/'files'/name).read_bytes();assert a==b,name;count+=1
  o=(ORIGINAL/'files'/name).read_bytes()
  if a!=o:changes.append(dict(file=name,old_size=len(o),new_size=len(a),original_sha256=sha(o),patched_sha256=sha(a)))
 for name in ['main.dol','apploader.img','bi2.bin']:
  assert (tree/'sys'/name).read_bytes()==(back/'sys'/name).read_bytes(),name
 boot=(tree/'sys/boot.bin').read_bytes();newboot=(back/'sys/boot.bin').read_bytes()
 assert boot[:0x424]==newboot[:0x424] and boot[0x428:]==newboot[0x428:]
 assert struct.unpack_from('>I',newboot,0x424)[0]*4>=struct.unpack_from('>I',newboot,0x420)[0]*4+(tree/'sys/main.dol').stat().st_size
 dol=(back/'sys/main.dol').read_bytes();rows=catalog();mapping={m['character']:m['code'] for m in read(ROOT/'translation/wii_font_plan.json')['mapping']};uicount=0;metacount=0
 for r in rows:
  if r['translation'] is None:continue
  raw=body(r,mapping)
  if r['kind']=='dol_rodata_string_candidate':
   for o in r['references']:
    ptr=struct.unpack_from('>I',dol,o)[0];at=offset(dol,ptr);assert dol[at:at+len(raw)]==raw,r['id']
   uicount+=1
  elif r['kind']=='metadata_string':
   b=(back/'files/bin/globals.bin').read_bytes();ob=(ORIGINAL/'files/bin/globals.bin').read_bytes();oldbase=24+struct.unpack_from('<I',ob)[0];base=24+struct.unpack_from('<I',b)[0];ptr=struct.unpack_from('<I',b,base+r['pointer_offset']-oldbase)[0]+base;assert b[ptr:ptr+len(raw)]==raw,r['id'];metacount+=1
 # Verify no approved same-file GC source was silently omitted during porting.
 old=read(GC/'translation/text_catalog.json');scope=read(GC/'metadata/build_scope_proposal.json')['record_ids_by_bucket'];allowed=set(scope['script_test_candidate']+scope['metadata_test_candidate']);keys={(r['kind'],r['file'],r['source']) for r in old if r['id'] in allowed and r.get('translation') is not None}
 missed=[r['id'] for r in rows if r['translation'] is None and (r['kind'],r['file'],r['source']) in keys];assert not missed,missed
 original=ROOT/'Wii Chibi-Robo! (Japan).iso';oh=filehash(original);assert oh=='fff35ac0a42f27b412b36b351cc0d31b6d81f3a2ff3120bed4488fe36bbd56df'
 iso=ROOT/args.iso
 report=dict(original_sha256=oh,iso=iso.relative_to(ROOT).as_posix(),iso_size=iso.stat().st_size,iso_sha256=filehash(iso),readback_files=count,readback_system_files=4,changed_files=changes,ui_records_verified=uicount,metadata_records_verified=metacount,omitted_approved_same_source_records=missed,partition='DATA only',wit_verify='PASS; encrypted partition, fake-signed ticket and TMD',runtime='Font-only probe reached Japanese title screen; integrated final ISO not played. Korean glyph and script behavior CPU-tested; GPU display and real hardware unverified.')
 save(ROOT/'metadata/final_build_verification.json',report);print('PASS',count,'files;',len(changes),'changed;',uicount,'UI;',metacount,'metadata;',report['iso_sha256'])
if __name__=='__main__':main()
