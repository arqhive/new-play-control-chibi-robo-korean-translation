from port_common import *
from PIL import Image,ImageDraw
import numpy as np

def feature(im):
 a=np.array(im.convert('RGBA').resize((32,32),Image.Resampling.BILINEAR)).astype(float);a[:,:,:3]*=a[:,:,3:4]/255;return a

def main():
 rows=read(ROOT/'metadata/remaining_work.json')['graphics_inherited'];cat=read(ROOT/'metadata/graphics_catalog.json');feat=np.stack([feature(Image.open(ROOT/t['png'])) for t in cat]);result=[]
 for k,r in enumerate(rows):
  im=Image.open(r['gc_png']);dist=np.mean(abs(feat-feature(im)),axis=(1,2,3))+np.array([abs(np.log((t['width']/t['height'])/(im.width/im.height)))*30 for t in cat]);idx=np.argsort(dist)[:3]
  result.append(dict(code=r['code'],candidates=[dict(id=cat[i]['id'],score=float(dist[i]),png=cat[i]['png']) for i in idx],observation=r['observation']))
 for batch in range(2):
  sheet=Image.new('RGB',(1000,14*140),'#444');d=ImageDraw.Draw(sheet)
  for k,r in enumerate(result[batch*14:batch*14+14]):
   src=rows[batch*14+k]
   for col,(label,p) in enumerate([(r['code'],src['gc_png'])]+[(t['id'][-34:]+' %.2f'%t['score'],str(ROOT/t['png'])) for t in r['candidates']]):
    im=Image.open(p).convert('RGBA');im.thumbnail((235,115));d.text((col*250,k*140+2),label,fill='white');sheet.paste(im,(col*250,k*140+22),im)
  sheet.save(ROOT/f'work/remaining-images/rematch-{batch}.png')
 save(ROOT/'metadata/graphics_hold_rematch.json',result)
 print('Compared',len(rows),'holds with',len(cat),'Wii textures')
if __name__=='__main__':main()
