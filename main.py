#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json, re, glob, os
from bs4 import BeautifulSoup

def norm(s):
    return re.sub(r'\s+', ' ', s.replace('\u3000',' ')).strip()

def extract_block(txt):
    m = re.search(r'系別\(Department\)：([^　]+)', txt)
    return m.group(1) if m else None

def is_course_row(tds):
    if len(tds) < 15:
        return False
    seq = norm(tds[1].get_text()).rstrip('　')
    return seq.isdigit()

def parse_html(html, source):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    block = None
    out = []
    for tr in rows:
        tds = tr.find_all("td")
        txt = tr.get_text(" ", strip=True)
        if '系別(Department)：' in txt:
            b = extract_block(txt)
            if b:
                block = b
            continue
        if not is_course_row(tds):
            continue

        grade      = norm(tds[0].get_text())
        seq        = norm(tds[1].get_text()).rstrip('　')
        code       = norm(tds[2].get_text())
        major      = norm(tds[3].get_text()) or None
        term_order = norm(tds[4].get_text())
        clazz      = norm(tds[5].get_text())
        group_div  = norm(tds[6].get_text()) or None
        required   = norm(tds[7].get_text())
        credits    = norm(tds[8].get_text())
        group_     = norm(tds[9].get_text())
        title_full = norm(tds[10].get_text())
        cap        = norm(tds[11].get_text())
        teacher    = re.sub(r'\(.*?\)', '', norm(tds[12].get_text())).replace(" ", "")
        t1         = norm(tds[13].get_text())
        t2         = norm(tds[14].get_text()) if len(tds) > 14 else ""

        english = '全英語授課' in title_full
        note = '淡水校園上課' if '淡水校園' in title_full else None
        title = title_full.replace('◇全英語授課','').replace('淡水校園上課','').strip()

        rec = {
            "source": source,
            "dept_block": block,           # e.g., TNUOB / TNUOE
            "grade": grade,
            "seq": seq,
            "code": code,
            "major": major,
            "term_order": term_order,
            "class": clazz,
            "group_div": group_div,
            "required": required,
            "credits": int(credits) if credits.isdigit() else credits,
            "group": group_,
            "title": title,
            "cap": int(cap) if cap.isdigit() else cap,
            "teacher": teacher,
            "times": [t for t in (t1, t2) if t],
            "english_taught": english
        }
        if note: rec["note"] = note
        out.append(rec)
    return out

def read_text(path):
    # Try UTF-8 then Big5
    for enc in ("utf-8", "cp950", "big5"):
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.read()
        except Exception:
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data", help="folder with .htm files")
    ap.add_argument("-o","--output", default="courses.json")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    seen_seq = set()
    records = []
    for path in sorted(glob.glob(os.path.join(args.dir, "*.htm"))):
        fname = os.path.basename(path)
        html = read_text(path)
        parsed = parse_html(html, source=fname)
        for rec in parsed:
            seq = rec.get("seq")
            if seq in seen_seq:
                print(f"Skipped duplicate seq {seq} from {fname}")
                continue
            seen_seq.add(seq)
            records.append(rec)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2 if args.pretty else None)

    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
