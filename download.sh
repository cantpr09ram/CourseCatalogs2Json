#!/usr/bin/env bash
set -euo pipefail

# 計算 ROC 學年度 + 學期
year=$(date +%Y)
month=$(date +%m)
roc_year=$((year - 1911))
if [ "$month" -ge 8 ] && [ "$month" -le 12 ]; then
  semester=1; school_year=$roc_year
elif [ "$month" -eq 1 ]; then
  semester=1; school_year=$((roc_year - 1))
else
  semester=2; school_year=$((roc_year - 1))
fi
code="${school_year}${semester}"

url="https://esquery.tku.edu.tw/acad/upload/${code}CLASS.RAR"
rar_path="file.rar"
out_dir="data"
tmpdir="$(mktemp -d)"

echo "Downloading ${url}..."
curl -fSL "$url" -o "$rar_path"
echo "Downloaded: $rar_path"


if ! command -v unar >/dev/null 2>&1; then
  echo "Error: unar not installed. On Ubuntu: sudo apt-get install -y unar"
  exit 1
fi


unar -quiet -o "$tmpdir" "$rar_path"

if [ -d "$tmpdir/CLASS/data" ]; then
  rsync -a "$tmpdir/CLASS/data/" "$out_dir/"
elif [ -d "$tmpdir/data" ]; then
  rsync -a "$tmpdir/data/" "$out_dir/"
else
  echo "Expected CLASS/data not found in archive"
  exit 1
fi

rm -rf "$tmpdir"
echo "Extracted CLASS/data -> $out_dir"
