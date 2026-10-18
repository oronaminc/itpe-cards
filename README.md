# 정보관리기술사 단어장

핸드폰으로 셀프 테스트하는 약어·두음·개념 암기 카드. 빌드 결과는 단일 HTML(`dist/index.html`).

## 빌드

```sh
python3 build.py        # data/*.json → src/template.html 의 {{CARDS_JSON}} 자리에 주입
                        # → dist/index.html (게시용), dist/preview.html (로컬 확인용, git 제외)
```

## 데이터 갱신

| 파일 | 형식 |
|---|---|
| `data/abbr.json` | `[{"abbr":"SLA","full":"Service Level Agreement","ko":"서비스 수준 협약 — 한 줄 뜻","cat":"IT경영"}]` |
| `data/dueum.json` | `[{"dueum":"기소카메오메보","topic":"SLA","items":["기본계약서", …],"cat":"IT경영"}]` |
| `data/concepts.json` | `[{"id":"pm-12","domain":"프로젝트관리","imp":"상","group":"…","topic":"…","keys":"…","def":"…","exam":"…","itpe":"1338"}]` |

- 파일을 덮어쓰고 `python3 build.py` 만 다시 돌리면 된다. 없는 파일은 빈 덱.
- `ko` 의 `—` 앞은 카드 뒷면에 크게, 뒤(한 줄 뜻)는 작게 나온다.
- 분야 필터는 데이터의 `cat` 값을 모아 만든다(순서: IT경영, 프로젝트관리, SW공학, 클라우드·인프라, CA·OS, 네트워크·통신, DB·데이터, AI, 보안, 표준·기관, 기타 → 그 밖의 값).
- `concepts.json` 은 볼트에서 다시 뽑을 수 있다(볼트는 읽기만 함):
  `python3 tools/extract_concepts.py ~/path/to/기술사 data/concepts.json`

## 진도 저장

- 카드 id: 약어 `a-<약어>`, 두음 `d-<토픽 두음>`, 개념 `c-<id>` (영숫자·`-` 외 문자는 `_xxxx` 로 인코딩).
  같은 약어/토픽이면 데이터 순서가 바뀌어도 진도가 유지된다.
- 게시 때 `capabilities: {db:{rules:[{path:"progress",read:"owner",write:"owner"}]}, user:{}}` 를 선언한다.
  소유자가 열면 `progress/<카드 id>` 문서(`{box,right,wrong,last,due}`)로 기기 간 동기화,
  그 밖(미리보기·다른 사람·저장소 없음)은 localStorage 폴백. 화면 오른쪽 위 칩에 저장 위치가 보인다.
- 라이트너 상자 0~4, 다음 복습: 0 즉시 · 1일 · 3일 · 7일 · 14일. 몰라요 → 0, 헷갈려요 → 유지, 알아요 → +1.
