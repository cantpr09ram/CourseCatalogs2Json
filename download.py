from datetime import datetime
import requests
import rarfile
import os

def convert_today_to_school_year_semester() -> str:
    today = datetime.today()
    year = today.year
    month = today.month

    roc_year = year - 1911

    if 8 <= month <= 12:
        semester = 1
        school_year = roc_year
    elif month == 1:
        semester = 1
        school_year = roc_year - 1
    else:
        semester = 2
        school_year = roc_year - 1

    return f"{school_year}{semester}"

def downloadExtract():
    url = f"https://esquery.tku.edu.tw/acad/upload/{convert_today_to_school_year_semester()}CLASS.RAR"
    rar_path = 'file.rar'
    extract_to = 'data'

    # Download the .rar file
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(rar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {rar_path}")
    else:
        print(f"Failed to download. Status code: {response.status_code}")
        exit()

    rarfile.UNRAR_TOOL = 'unrar'  # Ensure unrar is available

    try:
        with rarfile.RarFile(rar_path) as rf:
            for info in rf.infolist():
                if info.filename.startswith('CLASS/data/') and not info.is_dir():
                    relative_path = info.filename[len('CLASS/data/'):]  # Remove 'CLASS/data/' prefix
                    output_path = os.path.join(extract_to, relative_path)

                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    with rf.open(info) as source, open(output_path, 'wb') as target:
                        target.write(source.read())

        print(f"Extracted only CLASS/data/ files to: {extract_to}")
    except rarfile.Error as e:
        print(f"Extraction failed: {e}")

def main():
    downloadExtract()

if __name__ == "__main__":
    main()
