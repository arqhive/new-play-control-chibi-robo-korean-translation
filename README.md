# Wii로 즐기는 치비로보! 한글 패치

*Wiiであそぶ ちびロボ!* (Wii, 일본판 `R24J01`, Wiiであそぶセレクション / 북미판 *New Play Control! Chibi-Robo!*) 비공식 한국어 팬 패치입니다.
일본판 원문을 기준으로 번역했습니다.

**제작: arqhive** · **최신 버전: [v0.9](../../releases/tag/v0.9)**

- 대사, 메뉴, 아이템·레치커즈 설명, 도움말, 저장 문구, 전광판 문구를 한글화했습니다.
- 「치비컴」 로고 등 그림 글씨, 조작 안내·스트랩 안내 그림, 디스크 배너, HOME 메뉴를 한글화했습니다.
- 한글과 숫자·영문·기호를 G마켓 산스 Bold로 맞췄습니다.
- 영상 속 글자는 원문 그대로 두었습니다.
- **파일 단위 패처**라서 덤프마다 이미지 해시가 달라도 게임 파일만 같으면 적용됩니다.

게임큐브판 『ちびロボ!』 한글 패치는 [chibi-robo-korean-translation](https://github.com/arqhive/chibi-robo-korean-translation)에 있습니다.

> 이 저장소에는 **게임 데이터(디스크 이미지, 추출한 원문 대사, 원본 그래픽, 스크린샷)가 들어 있지 않습니다.**
> 패치를 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다.

## 사용자용: 패치 적용

### 준비물

- 일본판 디스크 이미지(`R24J01`). 북미판·유럽판과 게임큐브판에는 적용할 수 없습니다.
- Windows 10 이상. 따로 설치할 것은 없습니다.
- 빈 공간 약 10GB(작업용 파일 포함).

### 지원 형식

| 원본 | 결과 |
|---|---|
| ISO | ISO |
| WBFS | WBFS |
| CISO, WIA, WDF | ISO |
| RVZ, NKit | 지원 안 함. Dolphin 등에서 ISO로 바꾼 뒤 적용 |

### 적용 방법

1. [릴리즈 페이지](../../releases/latest)에서 `R24J_KPatch_v<버전>.zip`을 받아 압축을 풉니다.
2. 원본 이미지를 `패치하기.bat` 위에 끌어다 놓거나, 같은 폴더에 넣고 `패치하기.bat`을 더블클릭합니다.
3. 원본과 같은 폴더에 `Chibi-Robo! (Korean) [R24J01].iso`(원본이 WBFS면 `.wbfs`)가 생깁니다. 원본은 바뀌지 않습니다.

### 실행 환경

- **확인함**: Wii U vWii(USB Loader GX).

## 개발자용

- 번역문: [`translation/ko.json`](translation/ko.json)에 ID별 한국어 번역문만 들어 있습니다. `<숫자>`는 원문 제어 코드(이름 칸·색·대기 등) 자리라 그대로 둡니다.
- 도구: [`tools/`](tools)에 분석·글꼴·빌드·검증 도구 소스가 있고, [`patcher/`](patcher)와 [`tools/make_patcher.py`](tools/make_patcher.py)가 배포 패처입니다(Python 3.13, Pillow).
- 일본어 원문 추출본, 그림 작업 파일, 작업 상태 기록은 게임 데이터이거나 작업용이라 넣지 않았습니다. 그래서 이 저장소만으로는 바로 빌드되지 않고, 원본 이미지에서 추출부터 다시 해야 합니다.

## 변경 내역

전체 내역은 [`CHANGELOG.md`](CHANGELOG.md)에 있습니다.

## 크레딧·라이선스

- 이 저장소의 도구 코드, 한국어 번역문, 문서: [MIT License](LICENSE) (© 2026 arqhive).
- 글꼴: G마켓 산스(SIL OFL 1.1, [`licenses/GmarketSans-OFL.txt`](licenses/GmarketSans-OFL.txt)). 글꼴 파일은 저장소에 포함하지 않습니다.
- 패처 동봉 도구: wit v3.05a(GPL-2.0), xdelta3 3.1.0(Apache-2.0). 저장소에는 포함하지 않습니다.

## 면책

비공식 팬 번역이며 Nintendo, skip Ltd.와 관련이 없습니다. 「치비로보!」 관련 상표·저작권은 각 권리자에게 있습니다.
패치를 적용한 게임 파일의 배포를 금지합니다.
