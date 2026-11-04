from port_common import *
from decode_gx import decode,size,palette_rgba
from PIL import Image,ImageDraw
import re,collections,html

def u8(b):
 at=b.find(b'U\xaa8-');assert at>=0
 root=at+struct.unpack_from('>I',b,at+4)[0];n=struct.unpack_from('>I',b,root+8)[0];strings=root+n*12;stack=[]
 for i in range(1,n):
  while stack and i>=stack[-1][0]:stack.pop()
  typ,o,z=struct.unpack_from('>III',b,root+i*12);s=strings+(typ&0xffffff);name=b[s:b.index(0,s)].decode('utf-8');path='/'.join([p for _,p in stack]+[name])
  if typ>>24:stack.append((z,name))
  else:yield path,b[at+o:at+o+z]

def unwrap(b):
 if b[:4]==b'IMD5':b=b[32:]
 if b[:4]==b'LZ77':
  b=b[4:];assert b[0]==0x10;n=int.from_bytes(b[1:4],'little');out=bytearray();at=4
  while len(out)<n:
   flags=b[at];at+=1
   for bit in range(7,-1,-1):
    if len(out)>=n:break
    if flags&(1<<bit):
     a,c=b[at:at+2];at+=2;length=(a>>4)+3;dist=((a&15)<<8|c)+1
     for _ in range(length):out.append(out[-dist])
    else:out.append(b[at]);at+=1
  assert len(out)==n;b=bytes(out)
 return b

def main():
 rows=read(ROOT/'metadata/breft_catalog.json');b=(ORIGINAL/'files/eff/cb_robo.breft').read_bytes()
 assert struct.unpack_from('>H',b,6)[0]==11
 for r in rows:
  if not r.get('header_size_verified'):r['offset']+=32
  r['header_size_verified']=64;n=size(r['width'],r['height'],r['format']);im=decode(b[r['offset']:r['offset']+n],r['width'],r['height'],r['format']);im.save(ROOT/r['png'])
 save(ROOT/'metadata/breft_catalog.json',rows)
 sheet=Image.new('RGB',(800,((len(rows)+7)//8)*110),'#444444');d=ImageDraw.Draw(sheet)
 for i,r in enumerate(rows):
  im=Image.open(ROOT/r['png']);im.thumbnail((90,85));x=i%8*100;y=i//8*110;sheet.paste(im,(x,y),im);d.text((x,y+87),r['name'][:15],fill='white')
 sheet.save(ROOT/'work/breft-survey/sheet.png')
 # Inventory nested Wii banner resources without modifying the external system UI.
 out=ROOT/'work/banner-survey';out.mkdir(exist_ok=True);banner=[]
 def visit(data,prefix=''):
  for name,raw in u8(data):
   raw=unwrap(raw)
   name=prefix+name
   if raw[:4]==bytes.fromhex('0020af30'):
    _,n,table=struct.unpack_from('>III',raw)
    for i in range(n):
     at,pal=struct.unpack_from('>II',raw,table+8*i);h,w,f,o=struct.unpack_from('>HHII',raw,at);palette=None
     if pal:
      count=struct.unpack_from('>H',raw,pal)[0];pf,po=struct.unpack_from('>II',raw,pal+4);palette=palette_rgba(raw[po:po+count*2],pf)
     png=f'work/banner-survey/{len(banner):03}.png';decode(raw[o:o+size(w,h,f)],w,h,f,palette).save(ROOT/png);banner.append(dict(name=name,index=i,width=w,height=h,format=f,png=png))
   elif b'U\xaa8-' in raw[:256]:visit(raw,name+'/')
   else:banner.append(dict(name=name,size=len(raw),decoded=False))
 visit((ORIGINAL/'files/opening.bnr').read_bytes());save(ROOT/'metadata/banner_inventory.json',banner)
 cat=read(ROOT/'translation/text_catalog.json');pending=[r for r in cat if r['translation'] is None and not r.get('exclusion') and re.search('[\u3040-\u30ff\u3400-\u9fff]',r['source'])]
 save(ROOT/'metadata/remaining_text.json',pending)
 gc=read(GC/'metadata/graphics_recheck_v04_observations.json')['groups'];done={'G0204','G2281','G2282','G2283','G2284'};gcat=read(ROOT/'metadata/graphics_catalog.json');byhash=collections.defaultdict(list)
 for r in gcat:byhash[r['pixel_sha256']].append(r)
 remaining=[]
 for r in gc:
  if r['code'] in done:continue
  matches=byhash.get(r['pixel_sha256'],[])
  remaining.append(dict(code=r['code'],observation=r['observation'],gc_png=str(GC/r['png']),wii_matches=[t['id'] for t in matches],png=matches[0]['png'] if matches else None,status='exact_pixel_match' if matches else 'wii_counterpart_unconfirmed'))
 newids=['tpl/logo.tpl#tpl-000','tpl/logo.tpl#tpl-001','tpl/logow.tpl#tpl-000','tpl/logow.tpl#tpl-001','tpl/misc.tpl#tpl-268','tpl/misc.tpl#tpl-269']
 new=[r for r in gcat if r['id'] in newids]
 report=dict(text_count=len(pending),text_by_file=dict(collections.Counter(r['file'] for r in pending)),graphics_inherited=remaining,graphics_wii_new=new,banner='opening.bnr unchanged; nested archive inventory available',video='karaoke_teriyaki.thp unchanged',scope_note='Candidate inventory, not proof of exhaustive on-screen coverage. Unreadable GC counterparts remain unconfirmed unless pixel-exact.')
 save(ROOT/'metadata/remaining_work.json',report)
 page=ROOT/'work/remaining';page.mkdir(exist_ok=True);e=html.escape
 chunks=['<!doctype html><meta charset="utf-8"><title>Wii 치비로보 남은 작업</title><style>body{background:#292d32;color:#eee;font:17px sans-serif;margin:32px}img{max-width:650px;image-rendering:pixelated;background:#555}td{border:1px solid #777;padding:8px}pre{white-space:pre-wrap}</style><h1>Wii 치비로보 — 남은 작업</h1>',f'<p>미번역 일본어 후보 {len(pending)}항목. 디버그·미사용 가능 항목도 포함하며 실제 등장 여부는 미확인입니다.</p><h2>Wii 추가 그림</h2>']
 for r in new:chunks.append(f'<h3>{e(r["id"])}</h3><img src="../../{r["png"]}">')
 chunks.append('<h2>GC에서 이어진 판독 보류 그림</h2>')
 for r in remaining:chunks.append(f'<h3>{r["code"]} · {e(r["status"])}</h3><p>{e(r["observation"])}<br>{e(", ".join(r["wii_matches"]))}</p><img src="{("../../"+r["png"]) if r["png"] else Path(r["gc_png"]).as_uri()}">')
 chunks.append('<h2>별도 남은 범위</h2><p>Wii 배너·홈 버튼 시스템 화면은 원본 유지. 노래방 영상 karaoke_teriyaki.thp의 일본어도 원본입니다. 스크린 전체 전수 플레이 검증은 하지 않았습니다.</p><h2>미번역 텍스트 후보</h2><table><tr><th>ID</th><th>원문</th></tr>')
 for r in pending:chunks.append(f'<tr><td>{e(r["id"])}</td><td><pre>{e(r["source"])}</pre></td></tr>')
 chunks.append('</table>');(page/'index.html').write_text('\n'.join(chunks),'utf-8')
 print('Remaining',len(pending),'text;',len(remaining),'GC groups;',sum(bool(r['wii_matches']) for r in remaining),'pixel-exact Wii matches;',len(new),'Wii new graphics; banner entries',len(banner))
if __name__=='__main__':main()
