from port_common import *
from decode_gx import decode,size,palette_rgba
from PIL import Image,ImageDraw
import numpy as np
def main():
 out=ROOT/'work/graphics-survey';out.mkdir(parents=True,exist_ok=True);rows=[];errors=[]
 for p in sorted((ORIGINAL/'files').rglob('*')):
  if p.suffix not in ('.tpl','.brres'):continue
  b=p.read_bytes();file=p.relative_to(ORIGINAL/'files').as_posix()
  textures=[]
  if p.suffix=='.tpl':
   magic,n,table=struct.unpack_from('>III',b);assert magic==0x20af30
   for i in range(n):
    d,pal=struct.unpack_from('>II',b,table+i*8);h,w,fmt,at=struct.unpack_from('>HHII',b,d);palette=None
    if pal:
     count=struct.unpack_from('>H',b,pal)[0];pf,po=struct.unpack_from('>II',b,pal+4);palette=palette_rgba(b[po:po+count*2],pf)
    textures.append(dict(id=f'{file}#tpl-{i:03}',width=w,height=h,format=fmt,offset=at,header=d,palette=palette,kind='tpl'))
  else:
   at=0
   while True:
    at=b.find(b'TEX0',at)
    if at<0:break
    try:
     w,h,fmt=struct.unpack_from('>HHI',b,at+0x1c);data=at+struct.unpack_from('>I',b,at+0x10)[0];np_=at+struct.unpack_from('>I',b,at+0x14)[0]
     name=b[np_:b.index(0,np_)].decode('utf-8');assert 0<w<=2048 and 0<h<=2048 and fmt in (0,1,2,3,4,5,6,14)
     textures.append(dict(id=f'{file}#{name}',width=w,height=h,format=fmt,offset=data,header=at,palette=None,kind='tex0'))
    except Exception as e:errors.append(dict(file=file,offset=at,error=str(e)))
    at+=4
  for t in textures:
   try:
    im=decode(b[t['offset']:t['offset']+size(t['width'],t['height'],t['format'])],t['width'],t['height'],t['format'],t.pop('palette'))
    t['file']=file;t['pixel_sha256']=sha(struct.pack('>II',*im.size)+im.tobytes());t['png']=f'work/graphics-survey/{len(rows):04}.png';im.save(ROOT/t['png']);rows.append(t)
   except Exception as e:errors.append(dict(id=t['id'],error=str(e)))
 save(ROOT/'metadata/graphics_catalog.json',rows);save(ROOT/'metadata/graphics_decode_errors.json',errors)
 gc={t['id']:t for t in read(GC/'metadata/graphics_catalog_jp.json')['images']}
 selected=read(GC/'metadata/graphics_encoding_verification.json')['textures']+read(GC/'metadata/extra_graphics_drafts_v03.json')['textures']
 # Premultiplied RGB + alpha makes differently encoded transparent RGB irrelevant.
 def feature(im):
  a=np.array(im.resize((32,32),Image.Resampling.BILINEAR)).astype(float);a[:,:,:3]*=a[:,:,3:4]/255;return a
 features=np.stack([feature(Image.open(ROOT/t['png']).convert('RGBA')) for t in rows]);matches=[];sheet=Image.new('RGB',(900,len(selected)*140),'#444444');d=ImageDraw.Draw(sheet)
 for k,s in enumerate(selected):
  src=gc[s['texture']];path=src.get('png') or src.get('png_path') or src.get('image_path')
  if not path:
   print('GC keys',src);break
  im=Image.open(GC/path).convert('RGBA');f=feature(im);dist=np.mean(abs(features-f),axis=(1,2,3));ratio=np.array([abs(np.log((t['width']/t['height'])/(im.width/im.height))) for t in rows]);dist+=ratio*30
  inds=np.argsort(dist)[:5];best=[dict(id=rows[i]['id'],score=float(dist[i]),png=rows[i]['png'],format=rows[i]['format']) for i in inds]
  matches.append(dict(code=s['code'],gc_texture=s['texture'],gc_png=path,candidates=best))
  for j,(label,img) in enumerate([(s['code'],im)]+[(f'{rows[i]["id"][-35:]} {dist[i]:.1f}',Image.open(ROOT/rows[i]['png'])) for i in inds]):
   img.thumbnail((140,105));sheet.paste(img,(j*150,k*140+25),img if img.mode=='RGBA' else None);d.text((j*150,k*140+3),label,fill='white')
 save(ROOT/'metadata/graphics_reuse_candidates.json',matches);sheet.save(out/'matches.jpg');print('textures',len(rows),'errors',len(errors),'groups',len(matches))
if __name__=='__main__':main()
