#!/usr/bin/env python3
"""data/*.json 을 src/template.html 에 주입해 dist/index.html 을 만든다.

  python3 build.py            # dist/index.html + dist/preview.html
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PLACEHOLDER = "{{CARDS_JSON}}"
SOURCES = [("abbr", "abbr.json", ("abbr",)),
           ("dueum", "dueum.json", ("dueum", "topic")),
           ("concepts", "concepts.json", ("topic",))]
SKELETON = ('<!doctype html><html><head><meta charset=utf-8>'
            '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '</head><body>{}</body></html>')


def load(name, required):
    path = ROOT / "data" / name
    if not path.exists():
        print(f"[경고] {path.relative_to(ROOT)} 없음 → 빈 덱", file=sys.stderr)
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        sys.exit(f"[오류] {name}: 최상위가 배열이어야 합니다")
    bad = [i for i, row in enumerate(data)
           if not isinstance(row, dict) or not all(str(row.get(k, "")).strip() for k in required)]
    if bad:
        print(f"[경고] {name}: 필수 필드({', '.join(required)}) 빠진 행 {len(bad)}개 건너뜀 (index {bad[:5]}…)",
              file=sys.stderr)
    return [row for i, row in enumerate(data) if i not in set(bad)]


def main():
    cards = {key: load(fname, req) for key, fname, req in SOURCES}
    # '<' 를 전부 < 로 바꿔 </script>, <!-- 가 JSON 안에서 태그로 해석되지 않게 한다 (JSON 으로는 동일한 값)
    payload = json.dumps(cards, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    template = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    if template.count(PLACEHOLDER) != 1:
        sys.exit(f"[오류] template.html 에 {PLACEHOLDER} 가 정확히 한 번 있어야 합니다")
    page = template.replace(PLACEHOLDER, payload)

    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "preview.html").write_text(SKELETON.format(page), encoding="utf-8")

    counts = ", ".join(f"{k} {len(v)}" for k, v in cards.items())
    size = (out / "index.html").stat().st_size
    print(f"dist/index.html  {size / 1024:.1f} KB  ({counts})")


if __name__ == "__main__":
    main()
