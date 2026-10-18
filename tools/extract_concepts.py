#!/usr/bin/env python3
"""Obsidian 볼트의 우선순위 표 → data/concepts.json  (볼트는 읽기만 한다)

  python3 tools/extract_concepts.py <볼트 경로> [출력 경로=data/concepts.json]

- 원천: 50_분석/우선순위_{IT경영전략,프로젝트관리,소프트웨어공학}.md 표에서 중요도 상·출제예상 행
- def: 행에 링크된 ITPE 토픽의 10_원본/10_ITPE_지식관리/<도메인>/<id>_<토픽>/meta.json
       '키워드(암기법)' 의 [정의]/[개념] 블록 중 토픽과 맞는 것만, 80자 이내. 없으면 빈 문자열.
- exam: 표의 '기출·연관' 칸 + 같은 meta.json '기출문제' 의 종목·회차·교시
"""
import hashlib, glob
import json
import os
import re
import sys

FILES = [("it", "IT경영", "우선순위_IT경영전략.md"),
         ("pm", "프로젝트관리", "우선순위_프로젝트관리.md"),
         ("se", "SW공학", "우선순위_소프트웨어공학.md")]
# 정의 앞에 붙은 두음 덩어리 (원문 그대로 두면 정의 문장이 깨진다)
DEF_PREFIX_TRIM = {"83": "조프리 전가위자성"}


def cells(line):
    line = line.strip().strip("|")
    return [x.strip().replace("\\|", "|") for x in re.split(r"(?<!\\)\|", line)]


def clean(s):
    return re.sub(r"\s+", " ", s.replace("​", " ").replace("\xa0", " ")).strip()


def norm(s):
    s = re.sub(r"\([^)]*\)", "", s.lower())
    return re.sub(r"[^0-9a-z가-힣]", "", s)


def parts(s):
    ps = [norm(s)] + [norm(x) for x in re.split(r"[/,]", s)]
    return [p for p in ps if len(p) >= 2]


def same(a, b):
    for x in parts(a):
        for y in parts(b):
            if x == y:
                return True
            sh, lo = sorted((x, y), key=len)
            if sh in lo and len(sh) / len(lo) >= 0.6:
                return True
    return False


def short(s):
    s = clean(s).lstrip(":-–* ").strip()
    g = re.search(r"[가-힣][A-Z]{2,}", s[25:])        # 다음 문장이 붙어 있는 곳에서 자르기
    if g:
        s = s[:25 + g.start() + 1]
    g = re.search(r"(?<=[가-힣])- | \*\* ", s[25:])
    if g:
        s = s[:25 + g.start()].rstrip()
    if len(s) > 80:
        s = s[:78].rstrip(" ,·-") + "…"
    return s


def candidates(t):
    out = []
    for m in re.finditer(r"\[(정의|개념)\]", t):
        pre = t[max(0, m.start() - 30):m.start()].rstrip(" ​\n\xa0")
        pre = re.split(r"[\]​\n\xa0]|\d+\.\s", pre)[-1].strip(" -*")
        body = t[m.end():]
        nb = re.search(r"\[[^\]]{1,20}\]", body)
        if nb:
            body = body[:nb.start()]
        b = body.strip()
        subs = list(re.finditer(r"(?:^|-)\s*([A-Za-z][A-Za-z ]{1,30}|[가-힣]{2,10})\s*:\s*", b))
        if len(subs) >= 2 and subs[0].start() == 0:      # "- MSA: … - Service Mesh: …" 묶음
            for i, sm in enumerate(subs):
                end = subs[i + 1].start() if i + 1 < len(subs) else len(b)
                out.append((sm.group(1).strip(), b[sm.end():end]))
        else:
            out.append((pre, body))
    return out


def get_def(text, topic, itpe_topic):
    cs = candidates(text)
    for label, body in cs:
        if label and same(label, topic):
            return short(body), True
    if same(topic, itpe_topic) and cs and (not cs[0][0] or same(cs[0][0], topic)):
        return short(cs[0][1]), True
    return "", same(topic, itpe_topic)


def get_exam(text):
    found = [(m.group(1), int(m.group(2)), m.group(3))
             for m in re.finditer(r"종목\s*(\S+)\s*\n?\s*회차\s*(\d+)\s*\n?\s*교시\s*(\d+)", text)]
    seen = []
    for kind, no, period in sorted(found, key=lambda x: -x[1]):
        s = f"{kind} {no}-{period}"
        if s not in seen:
            seen.append(s)
    return seen


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    vault = os.path.expanduser(sys.argv[1])
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "data", "concepts.json")
    kroot = os.path.join(vault, "10_원본", "10_ITPE_지식관리")
    index = {}
    for p in glob.glob(os.path.join(kroot, "*", "*", "meta.json")):
        index.setdefault(os.path.basename(os.path.dirname(p)).split("_", 1)[0], p)

    rows, stats = [], {}
    for prefix, domain, fname in FILES:
        lines = open(os.path.join(vault, "50_분석", fname), encoding="utf-8").read().splitlines()
        header, n = None, 0
        for ln in lines:
            if not ln.startswith("|"):
                continue
            c = cells(ln)
            if header is None and "토픽" in c:
                header = c
                continue
            if header is None or set("".join(c)) <= set("-: "):
                continue
            row = dict(zip(header, c))
            imp = row.get("중요도", "")
            if imp not in ("상", "출제예상"):
                continue
            n += 1
            m = re.search(r"ITPE_(\d+)_", row.get("ITPE 모범답안", ""))
            itpe = m.group(1) if m else ""
            df, exams = "", []
            if itpe in index:
                meta = json.load(open(index[itpe], encoding="utf-8"))
                sec = meta.get("섹션", {})
                df, ok = get_def((sec.get("키워드(암기법)") or {}).get("text", ""), row.get("토픽", ""), meta.get("토픽", ""))
                exams = get_exam((sec.get("기출문제") or {}).get("text", "")) if ok else []
            keys = clean(row.get("암기법", ""))
            km = re.match(r"^\[(개념|정의)\]\s*(.*)$", keys)
            if km and not df:
                df, keys = short(km.group(2)), ""
            trim = DEF_PREFIX_TRIM.get(itpe)
            if trim and df.startswith(trim):
                df = df[len(trim):].strip()
            exam = clean(row.get("기출·연관", ""))
            if exams:
                ex = ", ".join(exams[:6]) + (f" 외 {len(exams) - 6}" if len(exams) > 6 else "")
                exam = (exam + " / " if exam else "") + ex
            rows.append({"id": f"{prefix}-" + hashlib.sha1((domain + "|" + clean(row.get("토픽", ""))).encode()).hexdigest()[:8], "domain": domain, "imp": imp, "group": clean(row.get("대토픽", "")),
                         "topic": clean(row.get("토픽", "")), "keys": keys, "def": df, "exam": exam, "itpe": itpe})
        stats[domain] = n

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(stats, "합계", len(rows), "· def", sum(1 for r in rows if r["def"]), "· ITPE 링크", sum(1 for r in rows if r["itpe"]))


if __name__ == "__main__":
    main()
