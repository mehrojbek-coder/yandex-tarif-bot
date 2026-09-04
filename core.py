import json
import os
import re

from rapidfuzz import fuzz, process

with open(os.path.join(os.path.dirname(__file__), "tariffs.json"), encoding="utf-8") as f:
    TARIFFS: dict = json.load(f)

MODEL_INDEX: dict[str, dict[str, str]] = {}
ALL_MODEL_NAMES: list[str] = []
for tariff_name, payload in TARIFFS.items():
    for model, req in payload["models"].items():
        MODEL_INDEX.setdefault(model, {})[tariff_name] = req
        ALL_MODEL_NAMES.append(model)
ALL_MODEL_NAMES = sorted(set(ALL_MODEL_NAMES))

TARIFF_ORDER = ["Start", "Standart", "Komfort", "Electro", "Komfort+", "Biznes", "Premier"]


def format_result(model: str) -> str:
    rows = MODEL_INDEX.get(model)
    lines = [f"🚗 <b>{model}</b>\n"]
    if not rows:
        lines.append("Bu model ro'yxatda topilmadi.")
        return "\n".join(lines)

    matched_any = False
    for t in TARIFF_ORDER:
        if t not in rows:
            continue
        req = rows[t]
        if req.lower().startswith("ruxsat"):
            continue
        matched_any = True
        lines.append(f"✅ <b>{t}</b> — {req}")

    if not matched_any:
        lines.append("❌ Hech bir tarifga mos kelmaydi (barcha tariflarda ruxsat berilmagan).")

    lines.append(
        "\n<i>Eslatma: Start tarifida umumiy talab — 1993-yildan keyin ishlab chiqarilgan "
        "avtomobillar (Daewoo/Chevrolet Damas bundan mustasno). Yakuniy qaror doim "
        "Yandex Taxi xizmati tomonidan qabul qilinadi.</i>"
    )
    return "\n".join(lines)


def _normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r'\([^)]*\)', '', s)  # drop parenthetical (often Cyrillic/alt names)
    s = re.sub(r'[^a-z0-9+\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


_NORM_INDEX = {name: _normalize(name) for name in ALL_MODEL_NAMES}


def search_model(query: str, limit: int = 5):
    query = query.strip()
    if not query:
        return []
    for name in ALL_MODEL_NAMES:
        if name.lower() == query.lower():
            return [(name, 100)]

    nq = _normalize(query)
    scored = []
    for name, nname in _NORM_INDEX.items():
        if nname == nq:
            scored.append((name, 100))
            continue
        s1 = fuzz.token_sort_ratio(nq, nname)
        s2 = fuzz.WRatio(nq, nname)
        score = max(s1, s2)
        scored.append((name, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]
    return [(n, s) for n, s in top if s >= 60]


def extract_model_from_ocr_text(text: str) -> str | None:
    """
    O'zbekiston vehicle registration certificates (texnik pasport) always
    number their numbered fields the same way:
      1. Davlat raqam belgisi (plate number)
      2. Rusumi/Modeli (make/model)   <- what we want
      3. Rangi (color)
      4. Egasi (owner)
      5. Manzili (address)
      ...
    This numbering survives OCR/layout noise far better than searching for
    the "RUSUMI/MODELI" text label (which sits in a separate column and can
    get matched to the wrong value line). So we look for a line starting
    with "2" first, and only fall back to label-proximity / fuzzy matching
    if that fails.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        m = re.match(r'^2[\.\)\-:]?\s+(.{2,})$', line)
        if m:
            candidate = m.group(1).strip()
            compact = candidate.replace(" ", "")
            # sanity check: a plate number has no spaces and mixes digits
            # with letters (e.g. "90R252XA") — a model name doesn't look
            # like that, so skip only in that specific case.
            looks_like_plate = (
                " " not in candidate
                and any(c.isdigit() for c in compact)
                and any(c.isalpha() for c in compact)
                and 5 <= len(compact) <= 9
            )
            if not looks_like_plate:
                return candidate

    for i, line in enumerate(lines):
        upper = line.upper()
        if "RUSUMI" in upper or "MODELI" in upper or "МОДЕЛЬ" in upper:
            m = re.search(r'[:\-]\s*(.+)$', line)
            if m and len(m.group(1)) > 2:
                return m.group(1).strip()
            if i + 1 < len(lines):
                return lines[i + 1]

    # Fallback: fuzzy-match every line directly against known models.
    best_name, best_score = None, 0
    for line in lines:
        nline = _normalize(line)
        if len(nline) < 3:
            continue
        for name, nname in _NORM_INDEX.items():
            score = fuzz.token_sort_ratio(nline, nname)
            if score > best_score:
                best_name, best_score = name, score
    if best_score >= 78:
        return best_name
    return None
