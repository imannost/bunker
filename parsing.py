import requests
import csv
import json
from io import StringIO
from typing import Optional
import time
import csv as _csv

def parse_google_sheet_to_json(spreadsheet_id, gid, skip_rows, output_file: Optional[str] = None, timeout: Optional[float] = 5.0, retries: int = 2, backoff: float = 0.7):
 
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BunkerBot/1.0)"}

    last_exc = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            break
        except Exception as exc:
            last_exc = exc
            if attempt == retries:
                raise
            time.sleep(backoff * (attempt + 1))
    response.raise_for_status()
    response.encoding = "utf-8"

    lines = response.text.splitlines()[skip_rows:]
    csv_file = StringIO("\n".join(lines))

    reader = csv.DictReader(csv_file)

    columns = {}
    for row in reader:
        for key, value in row.items():
            if value and value.strip():
                columns.setdefault(key, []).append(value.strip())

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(columns, f, ensure_ascii=False, indent=4)
        print(f"✅ Данные сохранены в {output_file}")
    return columns


def parse_google_sheet_to_rows(spreadsheet_id, gid, skip_rows: int = 0, timeout: Optional[float] = 5.0, retries: int = 2, backoff: float = 0.7):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BunkerBot/1.0)"}

    last_exc = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            break
        except Exception as exc:
            last_exc = exc
            if attempt == retries:
                raise
            time.sleep(backoff * (attempt + 1))

    response.raise_for_status()
    response.encoding = "utf-8"

    lines = response.text.splitlines()[skip_rows:]
    csv_file = StringIO("\n".join(lines))
    reader = _csv.reader(csv_file)
    return [row for row in reader]