"""Execute Wii GOTO/MSG/SELECT handlers; mock only draw/audio calls."""
from port_common import *
from build_wii_payload import cpu,regnum,reg,body
from unicorn import UC_HOOK_CODE
from collections import defaultdict,Counter
def main():
 stage=ROOT/'work/patched';stage=stage/'DATA' if (stage/'DATA').exists() else stage
 dol=(stage/'sys/main.dol').read_bytes();u=cpu(dol)
 GOTO=0x800975c4;MSG=0x8009cff8;THREAD=0x81920000;MSGOBJ=0x81500000;STAGE=0x81000000;GLOBALS=0x81400000;STOP=0x81ffff00
 put=lambda a,v:u.mem_write(a,struct.pack('>I',v))
 get=lambda a:int.from_bytes(u.mem_read(a,4),'big')
 gb=(stage/'files/bin/globals.bin').read_bytes();base=struct.unpack_from('<I',gb,16)[0]+24;u.mem_write(GLOBALS,gb)
 put(0x8044c4a8+0xec,GLOBALS);put(0x8044c4a8+0xf8,GLOBALS+base);put(0x8044c1a4+0x150,STAGE)
 calls=[]
 def hook(c,pc,n,data):
  if pc==0x800a5f34:
   calls.append((c.reg_read(regnum(4)),c.reg_read(regnum(5))));c.reg_write(reg.UC_PPC_REG_PC,c.reg_read(reg.UC_PPC_REG_LR))
  elif pc==0x8003714c:c.reg_write(reg.UC_PPC_REG_PC,c.reg_read(reg.UC_PPC_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook)
 def invoke(a,op):
  for r,v in {1:0x817f0000,3:THREAD,4:op,5:0}.items():u.reg_write(regnum(r),v)
  u.reg_write(reg.UC_PPC_REG_LR,STOP);u.emu_start(a,STOP,count=10000);assert u.reg_read(reg.UC_PPC_REG_PC)==STOP
  return u.reg_read(regnum(3))
 rows=read(ROOT/'translation/text_catalog.json');groups=defaultdict(list);counts=Counter()
 for r in rows:
  if r['kind']=='script_message_candidate' and r['translation'] is not None:groups[r['file']].append(r)
 for f,rs in groups.items():
  b=(stage/'files'/f).read_bytes();ram=GLOBALS if f=='bin/globals.bin' else STAGE;pbase=base if ram==GLOBALS else 0
  if ram==STAGE:u.mem_write(ram,b)
  for r in rs:
   at=r['opcode_offset'];new=struct.unpack_from('<I',b,at+1)[0]+pbase;finish=struct.unpack_from('<I',b,new+1)[0]+pbase;op=b[new]
   u.mem_write(THREAD,bytes(0x80));put(THREAD+0x54,MSGOBJ)
   put(THREAD+4,ram+at+1);assert invoke(GOTO,3)==0 and get(THREAD+4)==ram+new
   put(MSGOBJ+0x45638,0);put(MSGOBJ+0x45600,1);put(MSGOBJ+0x804,0);before=len(calls)
   put(THREAD+4,ram+new+1);assert invoke(MSG,op)==1 and get(THREAD+4)==ram+new
   assert len(calls)==before+1 and calls[-1]==(op,ram+new+5)
   put(MSGOBJ+0x804,1);put(THREAD+4,ram+new+1);assert invoke(MSG,op)==1 and get(THREAD+4)==ram+new
   put(MSGOBJ+0x804,0);put(MSGOBJ+0x45614,2);put(THREAD+4,ram+new+1);assert invoke(MSG,op)==0 and get(THREAD+4)==ram+finish
   if op==43:assert get(THREAD+0x10)==2
   put(THREAD+4,ram+finish+1);assert invoke(GOTO,3)==0 and get(THREAD+4)==ram+r['end'];counts[str(op)]+=1
 save(ROOT/'metadata/script_cpu_verification.json',dict(records=sum(counts.values()),opcodes=dict(counts),handlers={'GOTO':hex(GOTO),'MSG_SELECT':hex(MSG)},draw_calls_mocked=len(calls),sound_mocked=True,entry_retry_resume_return_verified=True,selection_result_verified=True,stage_and_globals_bases_verified=True,runtime_rendering_verified=False))
 print('PASS real Wii script handlers:',dict(counts))
if __name__=='__main__':main()
