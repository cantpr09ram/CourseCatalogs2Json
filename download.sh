#!/usr/bin/env bash
set -euo pipefail

# 計算 ROC 學年度 + 學期
year=$(date +%Y)
month=$(date +%m)
roc_year=$((year - 1911))

# 6月 到 11月 為第 1 學期
if [ "$month" -ge 6 ] && [ "$month" -le 11 ]; then
  semester=1; school_year=$roc_year

# 12月 為第 2 學期 (尚未跨西元年，故維持當年)
elif [ "$month" -eq 12 ]; then
  semester=2; school_year=$roc_year

# 1月 到 5月 為第 2 學期 (已跨西元年，故學年減 1)
else
  semester=2; school_year=$((roc_year - 1))
fi

code="${school_year}${semester}"

# 顯示結果
echo "current date: ${year}年${month}月"
echo "current semester: ${code}"

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
