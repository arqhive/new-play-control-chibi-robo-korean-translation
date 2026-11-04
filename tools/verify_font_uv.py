"""Run real Wii glyph construction AND downstream UV arithmetic on dirty stacks.

The separate material/GX initializer is not executed by this test (Unicorn
cannot run its paired-single instructions). It does not set the caller's
conversion slots. This is a CPU regression test, not a GPU rendering test.
"""
from build_wii_payload import *
import math

def main():
 dol=(ROOT/'work/patched/sys/main.dol').read_bytes();plan=read(ROOT/'translation/wii_font_plan.json')['mapping']
 obj=0x81000000;string=0x81001000;width=0x81002000;sp=0x817f0000
 def check(u,m,pattern):
  u.mem_write(sp-0x200,bytes([pattern])*0x200)
  c=m['code'];u.mem_write(string,(c.to_bytes(2,'big') if c>255 else bytes([c]))+b'\0\0')
  for r,v in {1:sp,3:obj,4:string,5:0,6:width}.items():u.reg_write(regnum(r),v)
  u.reg_write(reg.UC_PPC_REG_LR,0x81ffff00)
  u.emu_start(0x802b3efc,0x802b4144,count=5000)
  assert u.reg_read(reg.UC_PPC_REG_PC)==0x802b4144
  # Skip only material initialization; execute original UV arithmetic verbatim.
  u.emu_start(0x802b4154,0x802b4198,count=100)
  assert u.reg_read(reg.UC_PPC_REG_PC)==0x802b4198
  uv=[struct.unpack('>d',u.reg_read(getattr(reg,f'UC_PPC_REG_FPR{n}')).to_bytes(8,'big'))[0] for n in (1,2)]
  scale=struct.unpack('>ff',bytes(u.mem_read(obj+0x34,8)))
  return uv,list(scale)
 # Restore the faulty v01 hook in memory to ensure this test detects the bug.
 old=bytearray(dol);o=offset(old,BASE);assert old[o:o+8]==bytes.fromhex('90e1006090e10068')
 old[o:o+8]=bytes.fromhex('6000000060000000')
 u=cpu(old);m=next(m for m in plan if m['character']=='처');bad=[]
 for pattern in (0,0xa5,0xff):
  uv,scale=check(u,m,pattern);assert any(not math.isfinite(v) or v!=0 for v in uv)
  bad.append(dict(stack_fill=hex(pattern),uv=[v if math.isfinite(v) else str(v) for v in uv]))
 u=cpu(dol);count=0
 for pattern in (0,0xa5,0xff):
  for m in plan:
   uv,scale=check(u,m,pattern)
   assert uv==[0.,0.] and scale==[1.,1.],(m['character'],pattern,uv,scale)
   count+=1
 save(ROOT/'metadata/font_uv_verification.json',dict(glyphs=len(plan),dirty_stack_patterns=3,cases=count,old_hook_failures=bad,fixed_uv=[0,0],fixed_scale=[1,1],actual_wii_uv_arithmetic=True,material_initializer_executed=False,gpu_verified=False))
 print('PASS',count,'glyph/dirty-stack cases; v01 bug reproduced with three patterns')
if __name__=='__main__':main()
