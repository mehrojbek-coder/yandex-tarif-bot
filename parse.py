import json, re

with open("raw_data.txt", encoding="utf-8") as f:
    raw = f.read()

blocks = re.split(r'\n(?=«[^»]+» tarifi\n)', raw.strip())

data = {}
for block in blocks:
    lines = block.strip().split("\n")
    header = lines[0]
    m = re.match(r'«([^»]+)» tarifi', header)
    if not m:
        continue
    tariff_name = m.group(1)
    entries = {}
    special_note = None
    for line in lines[1:]:
        line = line.rstrip()
        if not line.strip():
            continue
        if "\t" in line:
            parts = line.split("\t")
            model = parts[0].strip()
            req = parts[1].strip() if len(parts) > 1 else ""
            entries[model] = req
        else:
            # note lines (Start tariff general text, Premier general reqs)
            special_note = (special_note + " " + line) if special_note else line
    data[tariff_name] = {"note": special_note, "models": entries}

with open("tariffs.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

for k, v in data.items():
    print(k, "->", len(v["models"]), "models", "| note:", (v["note"][:50] + "...") if v["note"] else None)
