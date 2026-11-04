"""Reuse approved raster lettering; precise native-pixel compositing (user authorized)."""
from port_common import *
from PIL import Image,ImageDraw,ImageFont
import numpy as np,cv2
from scipy.ndimage import distance_transform_edt

OUT=ROOT/'graphics/drafts/wii-remaining-v01'
CAT={r['id']:r for r in read(ROOT/'metadata/graphics_catalog.json')}
ROWS=[]

def record(key,original,clean,result,edit,kind,source,text=None):
 folder=OUT/key;folder.mkdir(parents=True,exist_ok=True)
 a=np.array(original);b=np.array(result);assert np.array_equal(a[~edit],b[~edit]),key
 for n,im in [('original',original),('cleaned',clean),('korean',result),('edit-mask',Image.fromarray(edit.astype('uint8')*255))]:im.save(folder/(n+'.png'))
 result.resize((result.width*3,result.height*3),Image.Resampling.NEAREST).save(folder/'korean-3x.png')
 r=dict(key=key,kind=kind,target=source,dimensions=list(result.size),candidate_path=str((folder/'korean.png').relative_to(ROOT)),candidate_sha256=sha((folder/'korean.png').read_bytes()),changed_pixels=int(np.any(a!=b,2).sum()),outside_edit_mask_changed_pixels=0,text=text)
 ROWS.append(r)

def strap():
 for n,r in enumerate(read(ROOT/'metadata/strap_reuse_discovery.json')['references']):
  a=np.array(Image.open(ROOT/r['original_png']).convert('RGBA'));before=a.copy();clean=a.copy();edit=np.zeros(a.shape[:2],bool)
  prior=np.array(Image.open(ROOT/r['copied_reference']).convert('RGBA'));wide=n>=2;isb=n%2==1;delta=107 if wide else 0;dx=10 if wide else 16;dy=12
  # Select actual label strokes, not rectangular patches. The bottom ruby
  # begins at y=352, above the former erase box; the wrist fade also crosses
  # that boundary and must not be erased along with the text.
  rgb=before[:,:,:3];hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
  yy,xx=np.indices(edit.shape)
  cyan=(rgb[:,:,0]<rgb[:,:,1])|(rgb[:,:,0]<rgb[:,:,2])
  red=((rgb[:,:,0]>rgb[:,:,1])&(rgb[:,:,2]>=rgb[:,:,1]))|(((hsv[:,:,0]<8)|(hsv[:,:,0]>172))&(hsv[:,:,1]>0))
  wrist=(yy<364)&(xx>=166+(106 if wide else 0))&(xx<274+(106 if wide else 0))
  bottom=(yy>=352)&((cyan|red)|(~wrist&np.any(rgb!=255,2)))
  # The small gray caption is isolated below the blue illustration.
  x0,y0,x1,y1=(290+delta,216,630+delta,312) if isb else (250+delta,216,628+delta,286)
  caption=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&np.any(rgb!=255,2)
  clean[caption,:3]=255;edit|=caption
  # Reconstruct only colored glyph pixels. Inpainting preserves the faint
  # wrist gradient beneath the topmost ruby; untouched art stays byte-exact.
  restored=cv2.inpaint(rgb,bottom.astype('uint8')*255,3,cv2.INPAINT_TELEA)
  wrist=(yy<364)&(xx>=166+(106 if wide else 0))&(xx<274+(106 if wide else 0))
  restored[:,:,1]=np.minimum(restored[:,:,0],restored[:,:,1]);restored[:,:,2]=np.minimum(restored[:,:,1],restored[:,:,2])
  clean[bottom,:3]=255;clean[bottom&wrist,:3]=restored[bottom&wrist];edit|=bottom
  assert np.array_equal(clean[~edit],before[~edit])
  assert not np.any(clean[yy>=364,:3]!=255), 'bottom text residue'
  assert not np.any(clean[(yy>=352)&~wrist,:3]!=255), 'ruby residue outside wrist'
  result=clean.copy()
  # Transfer only existing Korean strokes; preserve original Wii hand/controller art.
  for x0,y0,x1,y1 in [(260+(112 if wide else 0),210,600+(112 if wide else 0),300 if isb else 276),(0,345,prior.shape[1],434)]:
   part=prior[y0:y1,x0:x1];mask=np.any(part[:,:,:3]<250,2)
   yy,xx=np.where(mask);yy+=y0;xx+=x0;assert ((yy+dy)<a.shape[0]).all() and ((xx+dx)<a.shape[1]).all()
   result[yy+dy,xx+dx]=prior[yy,xx];edit[yy+dy,xx+dx]=True
  record(f'strap-{n}',Image.fromarray(before),Image.fromarray(clean),Image.fromarray(result),edit,'tpl',r['wii_id'],'기존 A07~A10 한글 문구 재사용')

def controllers():
 fontfile=ROOT/'work/references/gmarket/GmarketSansBold.otf'
 labels=[((84,20,283,44),'이동/메뉴 선택'),((313,0,510,24),'카메라/메뉴 선택'),((313,25,478,50),'만지기 포인터'),((197,54,254,80),'줌'),((148,82,254,111),'카메라 모드'),((129,123,254,150),'장비 메뉴'),((415,79,510,106),'취소'),((386,119,478,147),'액션'),((386,150,451,178),'일시 정지'),((386,179,449,209),'지도'),((157,191,261,216),'Z 액션'),((157,216,243,241),'치비 아이')]
 for index in (268,269):
  t=CAT[f'tpl/misc.tpl#tpl-{index}'];im=Image.open(ROOT/t['png']).convert('RGBA');a=np.array(im);clean=a.copy();edit=np.zeros(a.shape[:2],bool);layer=Image.new('RGBA',im.size)
  # Independently trace the devices, wires and button symbols. Text bounds
  # cannot be used as an eraser: the upper labels overlap the remote's rim.
  protect=np.zeros(a.shape[:2],np.uint8)
  def poly(points):cv2.fillPoly(protect,[np.array(points,np.int32)],255)
  def rect(x0,y0,x1,y1):protect[y0:y1,x0:x1]=255
  def circle(x,y,r):cv2.circle(protect,(x,y),r,255,-1)
  poly([(257,63),(258,54),(262,46),(270,40),(280,38),(303,38),(315,42),(324,50),(329,61),(329,86),(326,105),(323,122),(321,148),(321,205),(322,218),(325,229),(324,236),(318,241),(265,241),(259,237),(256,229),(259,217),(264,214),(264,151),(263,137),(263,124),(260,112),(258,94)])
  # Nunchuk silhouette, cable and the left end of its three leader lines.
  poly([(0,106),(45,97),(64,99),(84,107),(105,125),(119,150),(127,175),(131,207),(118,211),(89,197),(69,178),(55,162),(29,177),(0,178)])
  rect(0,145,132,241);rect(6,140,15,232);rect(18,166,28,215);rect(24,205,134,214);rect(6,222,133,232);rect(116,207,130,239)
  rect(46,27,60,104);rect(61,20,84,45)
  rect(171,54,198,80);rect(122,81,150,110);circle(119,136,13)
  rect(131,191,157,215);rect(130,216,156,238)
  # Main remote connection lines and pointer leader, including all outlines.
  rect(286,9,311,45);rect(253,62,299,78);rect(256,85,300,103);rect(254,91,256,99);rect(253,127,286,146)
  rect(286,111,305,139);rect(296,126,356,141)
  rect(300,137,318,170);rect(311,155,355,170)
  rect(294,176,356,199)
  rect(327,84,357,102);cv2.ellipse(protect,(371,93),(23,23),0,0,360,255,-1)
  rect(394,79,412,106)
  for y in (121,151,181):rect(360,y,384,y+21)
  protect=(protect>0)&(a[:,:,3]>0)
  # This texture consists only of the traced art and Japanese label strokes.
  # Remove all label remnants, including black outlines and hidden CMPR RGB.
  oldmask=np.any(a!=0,2)&~protect;clean[oldmask]=0;edit|=oldmask
  moved_icons=[];pointer_overlay=np.zeros(a.shape[:2],bool)
  for k,(box,txt) in enumerate(labels):
   if index==269 and k==0:txt='이동'
   x0,y0,x1,y1=box
   if k in (3,4,5):x0+=3
   if k in (7,8,9):x0=390
   if k==6:x0=418
   if k in (10,11):x0=162
   if k==2:x0=313
   if k==0:x0=89
   # 1.5 native pixels of black outline, rendered at 4x. The previous
   # stroke_width=2 was only 0.5 px after downsampling.
   s=4;stroke=6;pad=12;font=ImageFont.truetype(str(fontfile),15*s);b=font.getbbox(txt)
   # LANCZOS left half-pixel grey rows under the bottom bars (모·드·도·포·소).
   # Try the 16 sub-pixel offsets at 4x and box-filter the one with the fewest
   # mid-grey interior pixels, so horizontal strokes land on whole pixels.
   def draw(oy,ox):
    q=Image.new('RGBA',(b[2]-b[0]+pad*2+s,b[3]-b[1]+pad*2+s))
    ImageDraw.Draw(q).text((pad-b[0]+ox,pad-b[1]+oy),txt,font=font,fill='white',stroke_width=stroke,stroke_fill=(0,0,0,255))
    q=q.resize((q.width//s,q.height//s),Image.Resampling.BOX);return q.crop(q.getbbox())
   def grey(q):
    v=np.array(q).astype(int);m=v[:,:,:3].min(2);return int(((v[:,:,3]>200)&(m>50)&(m<200)).sum())
   p=min((draw(oy,ox) for oy in range(s) for ox in range(s)),key=grey)
   if p.width>x1-x0:p=p.resize((x1-x0,p.height),Image.Resampling.LANCZOS)
   # Center the actual white glyphs (not the font's ascender/descent box)
   # against the adjacent button. The two free labels keep their own rows.
   centers=[32,12,37,66.5,96,136,92,131,161,191,202,226.5]
   pixels=np.array(p);gy,gx=np.where((pixels[:,:,3]>127)&(pixels[:,:,:3].min(2)>180))
   if k in (3,4):
    # Move each button+caption as one group toward its remote leader.
    # Align the visible right edges of 줌 and 드 on the same native pixel.
    new_x=248-int(gx.max());dx=new_x-x0
    ix0,iy0,ix1,iy1=(171,54,198,80) if k==3 else (122,81,150,110)
    sy,sx=np.where(protect[iy0:iy1,ix0:ix1]);sy+=iy0;sx+=ix0
    values=clean[sy,sx].copy();clean[sy,sx]=0;protect[sy,sx]=False;edit[sy,sx]=True
    assert not np.any(clean[sy,sx+dx,3]), 'Moved button overlaps artwork'
    clean[sy,sx+dx]=values;protect[sy,sx+dx]=True;edit[sy,sx+dx]=True
    assert np.array_equal(clean[sy,sx+dx],a[sy,sx])
    moved_icons.append(dict(label=txt,shift_x=int(dx),glyph_right_x=248,icon_pixels_preserved=True))
    x0=new_x
   glyph_center=(int(gy.min())+int(gy.max()))/2
   py=round(centers[k]-glyph_center)
   assert 0<=py and py+p.height<=im.height,(index,k,py,p.height)
   layer.alpha_composite(p,(x0,py))
   if k==2:
    # User requested the pointer label directly below 카 and touching the
    # remote tip, covering the old label traces at the rim. Keep the base
    # artwork intact; only the new label's actual ink may overlay it.
    pointer_overlay[py:py+p.height,x0:x0+p.width]=np.array(p)[:,:,3]>0
  l=np.array(layer);assert not np.any(l[:,:,3][protect&~pointer_overlay]), str(np.argwhere((l[:,:,3]>0)&protect&~pointer_overlay).tolist());layer=Image.fromarray(l)
  edit|=l[:,:,3]>0;result=Image.alpha_composite(Image.fromarray(clean),layer)
  assert np.array_equal(np.array(result)[protect&~pointer_overlay],clean[protect&~pointer_overlay])
  record(f'controller-{index}',im,Image.fromarray(clean),result,edit,'tpl',t['id'],[txt if not(index==269 and k==0) else '이동' for k,(_,txt) in enumerate(labels)])
  folder=OUT/f'controller-{index}';Image.fromarray(protect.astype('uint8')*255).save(folder/'art-protection-mask.png')
  ROWS[-1].update(art_protection_changed_pixels=int(np.any(np.array(result)[protect]!=clean[protect],axis=1).sum()),unrequested_art_changes=0,art_protected_pixels=int(protect.sum()),original_art_restored=True,user_requested_pointer_overlay_pixels=int((pointer_overlay&protect).sum()),moved_icons=moved_icons,outline_native_pixels=1.5,vertical_alignment='visible white glyph center to adjacent button center; max rounding 0.5 px')

def banner():
 # Reuse the actual approved imagegen syllables from the GC logo.
 lettering=Image.open(GC/'graphics/drafts/G0343/composite-v01/lettering-extracted.png').convert('RGBA');glyphs=[]
 for i in range(4):
  part=lettering.crop((round(lettering.width*i/5),0,round(lettering.width*(i+1)/5),lettering.height));a=np.array(part)[:,:,3];yy,xx=np.where(a>16);glyphs.append(part.crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1)))
 for r in read(ROOT/'metadata/banner_inventory.json'):
  if not r.get('png'):continue
  name=Path(r['name']).name
  choices={'rogo_ti':0,'rogo_bi':1,'rogo_ro':2,'rogo_bo':3};stem=next((k for k in choices if name in (k+'.tpl',k+'_s.tpl')),None)
  if not stem:continue
  original=Image.open(ROOT/r['png']).convert('RGBA');a=np.array(original);h,w=a.shape[:2];small=w<30
  rgb=a[:,:,:3];hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV);colored=(hsv[:,:,1]>170)&(hsv[:,:,2]>130)&(a[:,:,3]>200)
  points=np.column_stack(np.where(colored)[::-1]).astype('int32');hull=np.zeros((h,w),np.uint8);cv2.fillConvexPoly(hull,cv2.convexHull(points),255)
  interior=cv2.erode(hull,np.ones((3 if not small else 1,)*2,np.uint8))>0
  colors,counts=np.unique(rgb[colored],axis=0,return_counts=True);basecolor=colors[counts.argmax()]
  good=colored&(np.max(np.abs(rgb.astype(int)-basecolor),2)<4)
  ink=interior&(~good);ink=(cv2.dilate(ink.astype('uint8'),np.ones((3 if not small else 1,)*2,np.uint8))>0)&interior
  # These panels have a flat dominant fill. Sampling tinted antialias pixels
  # near old white strokes would reproduce a faint Japanese silhouette.
  clean=a.copy();clean[ink,:3]=basecolor
  factor=min((w*.68)/max(g.width for g in glyphs),(h*.76)/max(g.height for g in glyphs));g=glyphs[choices[stem]];g=g.resize((round(g.width*factor*4),round(g.height*factor*4)),Image.Resampling.LANCZOS)
  layer=Image.new('RGBA',(w*4,h*4));layer.alpha_composite(g,(round(w*2-g.width/2),round(h*2-g.height/2)));l=np.array(layer.resize((w,h),Image.Resampling.LANCZOS));l[:,:,3][~interior]=0
  result=np.array(Image.alpha_composite(Image.fromarray(clean),Image.fromarray(l)));result[:,:,3]=a[:,:,3];edit=ink|(l[:,:,3]>0)
  record('banner-'+name[:-4],original,Image.fromarray(clean),Image.fromarray(result),edit,'banner',r['name'],'치비로보'[choices[stem]])

def main():
 global OUT
 OUT.mkdir(parents=True,exist_ok=True);oldout=OUT;OUT=ROOT/'graphics/drafts/wii-strap-v02';strap();OUT=oldout;OUT=ROOT/'graphics/drafts/wii-controller-v05';controllers();OUT=oldout;banner();save(ROOT/'metadata/remaining_image_drafts.json',dict(images=ROWS,method='Reuse approved raster lettering and explicit Python precision compositing permission; no new image generation.'))
 # Readable contact sheet, each row at original scale where possible.
 sheet=Image.new('RGB',(1280,sum(max(180,r['dimensions'][1])+35 for r in ROWS)),'#444444');d=ImageDraw.Draw(sheet);y=0
 for r in ROWS:
  d.text((5,y+3),r['key'],fill='white');folder=ROOT/r['candidate_path'];folder=folder.parent
  for col,n in enumerate(('original','cleaned','korean')):
   im=Image.open(folder/(n+'.png'));im.thumbnail((416,max(180,r['dimensions'][1])));sheet.paste(im,(col*425,y+25),im)
  y+=max(180,r['dimensions'][1])+35
 sheet.save(ROOT/'work/remaining-images/comparison.png');print('Prepared',len(ROWS),'images')
if __name__=='__main__':main()
