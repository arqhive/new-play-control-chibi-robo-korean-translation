from port_common import *
from PIL import Image
import numpy as np

rows=[]
for n in range(4):
 d=ROOT/f'graphics/drafts/wii-strap-v02/strap-{n}'
 a=np.array(Image.open(d/'original.png'));b=np.array(Image.open(d/'cleaned.png'))
 k=np.array(Image.open(d/'korean.png'));mask=np.array(Image.open(d/'edit-mask.png'))>0
 encoded=np.array(Image.open(ROOT/f'work/remaining-images/encoded/strap-{n}.png'))
 x=300+(106 if n>=2 else 0)
 assert not np.any(b[364:,:,:3]!=255), (n,'text remained below wrist')
 assert not np.any(encoded[340:357,x:,:3]!=255), (n,'encoded ruby residue')
 assert np.array_equal(a[~mask],k[~mask]), (n,'outside mask changed')
 assert np.array_equal(a[:216],k[:216]), (n,'controller or upper illustration changed')
 rows.append(dict(key=f'strap-{n}',cleaned_nonwhite_below_wrist=0,encoded_residue_band_nonwhite=0,outside_edit_mask_changed_pixels=0,upper_illustrations_exact=True))
save(ROOT/'metadata/strap_cleanup_v05.json',dict(images=rows,method='Stroke color and antialias mask; only wrist/text overlap inpainted; native and enlarged visual review'))
print('PASS: four strap graphics; blank-region and original-art checks')
