#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import re
import glob
import os
from bs4 import BeautifulSoup

# normalize whitespace
def norm(s):
    return re.sub(r'\s+', ' ', s.replace('\u3000',' ')).strip()

def extract_block(txt):
    m = re.search(r'系別\(Department\)：([^　]+)', txt)
    return m.group(1) if m else None

# relax rule: accept row if seq is digit OR code exists
def is_course_row(tds):
    if len(tds) < 15:
        return False
    seq  = norm(tds[1].get_text()).rstrip('　')
    code = norm(tds[2].get_text())
    return seq.isdigit() or bool(code)

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
        # teacher: drop parentheses and remove all spaces
        teacher    = re.sub(r'\(.*?\)', '', norm(tds[12].get_text())).replace(" ", "")
        t1         = norm(tds[13].get_text())
        t2         = norm(tds[14].get_text()) if len(tds) > 14 else ""

        rec = {
            "source": source,
            "dept_block": block,
            "grade": grade,
            "seq": seq if seq else None,
            "code": code,
            "major": major,
            "term_order": term_order,
            "class": clazz,
            "group_div": group_div,
            "required": required,
            "credits": int(credits) if credits.isdigit() else credits,
            "group": group_,
            "title": title_full,
            "cap": int(cap) if cap.isdigit() else cap,
            "teacher": teacher,
            "times": [t for t in (t1, t2) if t],
        }
        out.append(rec)
    return out

# ---------- TA merge helpers ----------
def is_ta(teacher: str) -> bool:
    """Detect TA rows by teacher field after cleaning."""
    if not teacher:
        return False
    t = teacher.strip()
    return t.upper() == "TA" or t == "助教" or t.endswith("助教")

def same_core(a, b) -> bool:
    """Define 'almost the same' core attributes."""
    return (
        a.get("code") == b.get("code") and
        a.get("class") == b.get("class") and
        a.get("term_order") == b.get("term_order") and
        a.get("group_div") == b.get("group_div") and
        a.get("title") == b.get("title") and
        a.get("required") == b.get("required") and
        a.get("credits") == b.get("credits")
    )

def merge_into(base, ta_rec):
    # merge times (preserve order, dedupe)
    for t in ta_rec.get("times", []):
        if t and t not in base["times"]:
            base["times"].append(t)

    # merge teacher using commas, preserve order, dedupe
    def split_csv(s): return [x for x in (s or "").split(",") if x]
    base_list = split_csv(base.get("teacher"))
    ta_list   = split_csv(ta_rec.get("teacher"))
    seen = set(base_list)
    for name in ta_list:
        if name and name not in seen:
            base_list.append(name)
            seen.add(name)
    base["teacher"] = ",".join(base_list)

    # overwrite cap if TA has integer and base doesn't
    if (not isinstance(base.get("cap"), int)) and isinstance(ta_rec.get("cap"), int):
        base["cap"] = ta_rec["cap"]
    if not base.get("seq"):
        base["seq"] = ta_rec.get("seq")
    if base.get("source") != ta_rec.get("source"):
        base["source"] = f"{base.get('source')};{ta_rec.get('source')}"

def dedupe_by_seq(records, verbose=False):
    """Keep the first occurrence of each non-empty seq. Drop later duplicates."""
    seen = set()
    out = []
    for r in records:
        seq = r.get("seq")
        if seq and seq in seen:
            if verbose:
                print(f"Removed duplicate by seq: {seq} ({r.get('code')}/{r.get('class')})")
            continue
        if seq:
            seen.add(seq)
        out.append(r)
    return out

def read_text(path):
    """Try UTF-8 then cp950/Big5. Fall back to UTF-8 with errors ignored."""
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

    output = []
    prev = None

    # stream records in file order; merge TA rows into the immediate previous record if 'almost the same'
    for path in sorted(glob.glob(os.path.join(args.dir, "*.htm"))):
        fname = os.path.basename(path)
        html = read_text(path)
        for rec in parse_html(html, source=fname):
            if prev and is_ta(rec.get("teacher")) and same_core(prev, rec):
                merge_into(prev, rec)
                continue  # merged into prev, do not append a new row
            output.append(rec)
            prev = output[-1]
    output = dedupe_by_seq(output, verbose=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2 if args.pretty else None)

    print(f"Wrote {len(output)} records to {args.output}")

if __name__ == "__main__":
    main()