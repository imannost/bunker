import requests
import csv
import json
from io import StringIO

def parse_google_sheet_to_json(spreadsheet_id, gid, skip_rows, output_file="result.json"):
 
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
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

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(columns, f, ensure_ascii=False, indent=4)

    print(f"✅ Данные сохранены в {output_file}")
    return columns
