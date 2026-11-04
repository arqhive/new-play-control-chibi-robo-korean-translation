from port_common import *
from PIL import Image,ImageDraw
import numpy as np
from decode_gx import decode,size
from verify_graphics_encoding import encode

def rgba8(im):
 a=np.array(im.convert('RGBA'));w,h=im.size;out=bytearray()
 for y in range(0,align(h,4),4):
  for x in range(0,align(w,4),4):
   block=np.zeros((4,4,4),np.uint8);hh=min(4,h-y);ww=min(4,w-x)
   if hh>0 and ww>0:block[:hh,:ww]=a[y:y+hh,x:x+ww]
   f=block.reshape(16,4);out.extend(f[:,[3,0]].tobytes());out.extend(f[:,[1,2]].tobytes())
 return bytes(out)
def main():
 old=read(GC/'metadata/graphics_encoding_verification.json')['textures']+read(GC/'metadata/extra_graphics_drafts_v03.json')['textures'];old={r['code']:r for r in old}
 specs=[('G0146','tpl/misc.tpl#tpl-087'),('G0146','tpl/Amisc.tpl#tpl-087'),('G0343','tpl/title.tpl#tpl-000'),('G0344','tpl/misc.tpl#tpl-247'),('G0344','tpl/Amisc.tpl#tpl-247'),('G0200','tpl/misc.tpl#tpl-145'),('G0204','tpl/misc.tpl#tpl-149'),('G0225','tpl/misc.tpl#tpl-170'),('G0226','tpl/misc.tpl#tpl-171'),('G0235','tpl/misc.tpl#tpl-180')]
 cat={r['id']:r for r in read(ROOT/'metadata/graphics_catalog.json')};out=ROOT/'work/graphics-port';out.mkdir(exist_ok=True);files={};report=[]
 for code,id in specs:
  t=cat[id];s=old[code];src=GC/s['candidate_path'];assert sha(src.read_bytes())==s['candidate_sha256']
  image=Image.open(src).convert('RGBA');target_size=(t['width'],t['height'])
  if image.size!=target_size:image=image.resize(target_size,Image.Resampling.LANCZOS)
  file=t['file']
  if file not in files:files[file]=bytearray((ORIGINAL/'files'/file).read_bytes())
  b=files[file];fmt=t['format'];original=Image.open(ROOT/t['png']).convert('RGBA')
  if code in ('G0200','G0204','G0225','G0226','G0235'):
   # TPL has absolute offsets and per-image format; append avoids moving any other image.
   data=rgba8(image);fmt=6;at=align(len(b));b.extend(bytes(at-len(b)));b.extend(data);struct.pack_into('>II',b,t['header']+4,fmt,at)
  else:
   at=t['offset'];n=size(*target_size,fmt);data,_,_=encode(bytes(b[at:at+n]),image,fmt);b[at:at+n]=data
  result=decode(data,*target_size,fmt);result.save(out/(id.replace('/','_').replace('#','_')+'.png'))
  # All RGBA8 adopted exceptions are pixel exact; other formats retain native quantization.
  if fmt==6:assert result.tobytes()==image.tobytes()
  approved=ROOT/'graphics/approved'/f'{code}-wii-{len(report):02}.png';image.save(approved)
  report.append(dict(code=code,id=id,source=str(src),approved=str(approved.relative_to(ROOT)),sha256=sha(approved.read_bytes()),source_format=t['format'],format=fmt,dimensions=list(target_size),png_exact=fmt==6,decoded=str((out/(id.replace('/','_').replace('#','_')+'.png')).relative_to(ROOT))))
 stage=ROOT/'work/patched';stage=stage/'DATA' if (stage/'DATA').exists() else stage
 for f,b in files.items():
  (stage/'files'/f).write_bytes(b)
  # Every entry's offset and encoded extent is valid after extension.
  magic,n,table=struct.unpack_from('>III',b)
  for i in range(n):
   d,pal=struct.unpack_from('>II',b,table+8*i);h,w,fmt,a=struct.unpack_from('>HHII',b,d);assert a+size(w,h,fmt)<=len(b)
 save(ROOT/'metadata/graphics_port.json',dict(textures=report,files=[dict(path=f,sha256=sha(b),size=len(b)) for f,b in files.items()]))
 sheet=Image.new('RGB',(780,len(report)*150),'#454545');d=ImageDraw.Draw(sheet)
 for i,x in enumerate(report):
  d.text((5,i*150+3),x['id'],fill='white')
  for j,im in enumerate([Image.open(ROOT/cat[x['id']]['png']),Image.open(ROOT/x['decoded'])]):
   im.thumbnail((370,120));sheet.paste(im,(j*390,i*150+25),im)
 sheet.save(out/'comparison.png');print('PASS',len(report),'textures',len(set(r['code'] for r in report)),'groups')
if __name__=='__main__':main()
