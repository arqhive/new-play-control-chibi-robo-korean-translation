from port_common import *
import html,shutil

def main():
 inj=read(ROOT/'metadata/remaining_image_injection.json');remaining=read(ROOT/'metadata/remaining_work.json');matches={r['code']:r for r in read(ROOT/'metadata/graphics_hold_rematch.json')};cat={r['id']:r for r in read(ROOT/'metadata/graphics_catalog.json')}
 for r in remaining['graphics_inherited']:
  if r['code']=='G0493':r['status']='wii_counterpart_unconfirmed';continue
  best=matches[r['code']]['candidates'][0];r['png']=best['png']
  if not r['wii_matches']:r['wii_matches']=[best['id']];r['status']='visual_counterpart_confirmed_reading_unresolved'
 remaining['graphics_wii_new_completed']=remaining.pop('graphics_wii_new',[]) or remaining.get('graphics_wii_new_completed',[]);remaining['graphics_wii_new']=[]
 remaining['banner']='8 logo syllable textures translated; IMET titles/description, animation, exclamation, TM and robot kept unchanged.'
 remaining['image_completion_report']='work/remaining-images/index.html';save(ROOT/'metadata/remaining_work.json',remaining)
 review=ROOT/'work/remaining-images/index.html';e=html.escape
 parts=['<!doctype html><meta charset="utf-8"><title>Wii 추가 그림 완료</title><style>body{background:#30343a;color:#eee;font:17px sans-serif;margin:24px}img{max-width:100%;height:auto;background:#555}section{margin-bottom:40px}.row{display:flex;gap:12px}.row>div{flex:1;min-width:0}p{line-height:1.65}a{color:#8cf}</style><h1>추가 그림 14장 완료</h1><p>왼쪽 원본 · 가운데 글자 제거 · 오른쪽 게임 형식 재읽기.<br>스트랩 안내 4장, 조작 안내 2장, 배너 글자 8장. 각 그림의 편집 마스크 밖 변경은 PNG 및 게임 형식 재읽기에서 0픽셀입니다.<br>조작 안내 2장은 RGBA8 무손실 형식이며, 배너 및 안내는 원래 형식을 유지했습니다. 실제 게임 화면은 미확인입니다.</p>']
 for r in inj['images']:
  path=ROOT/r['candidate_path'];target=ROOT/'graphics/approved/wii-extra'/path.parent.name/'korean.png';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
  r['approved_path']=str(target.relative_to(ROOT));r['visual_review']='native and enlarged PNG plus encoded result inspected'
  folder=path.parent;parts.append(f'<section><h2>{e(r["key"])}</h2><p>{e(r["target"])} · {r["dimensions"]} · 마스크 밖 변경 0픽셀</p><div class="row">')
  for label,p in [('원본',folder/'original.png'),('제거',folder/'cleaned.png'),('최종',ROOT/'work/remaining-images/encoded'/(r['key']+'.png'))]:parts.append(f'<div>{label}<br><a href="{p.as_uri()}"><img src="{p.as_uri()}"></a></div>')
  parts.append('</div></section>')
 parts.append('<h2>남은 그림 보류</h2><p>27묶음은 Wii 대응 그림을 확인했지만 작은 글자·도장의 원문 판독이 미확정입니다. G0493 한 묶음은 Wii 대응본을 찾지 못했습니다. 원래 영어 문구는 번역 대상에서 제외하며, 읽을 수 없는 부분을 추측하여 새 문구로 바꾸지 않았습니다. 영상 자막은 이번 이미지 작업에서 수정하지 않았습니다.</p>')
 for r in remaining['graphics_inherited']:
  p=ROOT/r['png'] if r['png'] else Path(r['gc_png']);parts.append(f'<h3>{r["code"]} · {e(r["status"])}</h3><p>{e(", ".join(r["wii_matches"]))}</p><img src="{p.as_uri()}" style="image-rendering:pixelated;min-width:128px;max-width:500px">')
 review.write_text('\n'.join(parts),'utf-8');save(ROOT/'metadata/remaining_image_injection.json',inj)
 # Replace the earlier open remaining page with current status and original text list.
 pending=read(ROOT/'metadata/remaining_text.json');p=ROOT/'work/remaining/index.html'
 s=['<!doctype html><meta charset="utf-8"><title>남은 작업</title><style>body{font:17px sans-serif;margin:32px;background:#30343a;color:#eee}a{color:#9df}td{border:1px solid #777;padding:8px}pre{white-space:pre-wrap}</style><h1>남은 작업</h1><p>안내·배너 14장 완료. <a href="../remaining-images/index.html">그림 비교와 보류 목록 보기</a></p><p>판독 보류 그림 27묶음, Wii 대응 미확인 G0493 1묶음. 노래방 영상은 원문 유지. 미번역 일본어 후보 380항목(디버그·미사용 가능 항목 포함)은 이번 작업에서 수정하지 않았습니다.</p><table>']
 for r in pending:s.append(f'<tr><td>{e(r["id"])}</td><td><pre>{e(r["source"])}</pre></td></tr>')
 s.append('</table>');p.write_text('\n'.join(s),'utf-8')
 print('Published review, copied 14 approved PNGs, updated remaining inventory')
if __name__=='__main__':main()
