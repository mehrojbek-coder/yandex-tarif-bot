# Yandex Taxi Tarif-Bot (Toshkent)

Telegram bot: mashina markasi/modeli **matn** yoki **texnik pasport rasmi** orqali yuborilsa,
Yandex Taxi (Toshkent)ning qaysi tariflariga (Start / Standart / Komfort / Electro / Komfort+ /
Biznes / Premier) mos kelishini va qaysi yildan ekanligini aytib beradi.

## Fayllar

- `tariffs.json` — barcha 7 tarifning to'liq mashina ro'yxati (~3200 yozuv), strukturaga solingan.
- `core.py` — qidiruv (fuzzy-search) va natijani formatlash logikasi (Telegramdan mustaqil, test qilinadigan).
- `bot.py` — aiogram 3 asosidagi Telegram bot (matn va rasm handlerlari).
- `parse.py` — `raw_data.txt`dan `tariffs.json` yasovchi bir martalik skript (ma'lumot yangilanganda qayta ishlatish mumkin).
- `raw_data.txt` — Yandex Pro sahifasidan olingan xom matn.

## O'rnatish

```bash
pip install -r requirements.txt
```

Rasm orqali qidiruv (OCR) ishlashi uchun serverda **Tesseract OCR** ham o'rnatilgan bo'lishi kerak:

```bash
apt-get install -y tesseract-ocr tesseract-ocr-uzb tesseract-ocr-rus
```

> Eslatma: agar `tesseract-ocr-uzb` paketi mavjud bo'lmasa, `lang="rus+eng"` bilan ham ishlaydi,
> lekin aniqlik pastroq bo'lishi mumkin — texnik pasportlar lotin-o'zbek va rus tillarida aralash.

## Ishga tushirish (lokal)

```bash
export BOT_TOKEN="123456:ABC-DEF..."
python3 bot.py
```

## Railway'ga deploy qilish

1. Ushbu papkani (yoki GitHub reponi) Railway loyihasiga ulang.
2. `Settings → Variables`ga `BOT_TOKEN` qo'shing (BotFather'dan olingan token).
3. Build/Start buyrug'i avtomatik `requirements.txt`ni topadi. Kerak bo'lsa Start Command:
   ```
   python3 bot.py
   ```
4. Agar OCR (rasm orqali qidiruv) kerak bo'lsa, `nixpacks.toml` yoki Dockerfile orqali
   `tesseract-ocr` paketini environment'ga qo'shish kerak (Railway'ning standart Python
   image'ida tesseract yo'q — shu sabab Dockerfile bilan deploy qilish tavsiya etiladi).

### Dockerfile bilan deploy qilish (OCR uchun tavsiya etiladi)

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-rus && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "bot.py"]
```

## Cheklovlar

- Rasm orqali OCR aniqligi texnik pasport sifatiga (yorug'lik, burchak, fokus) bog'liq.
  Model noto'g'ri o'qilsa, bot foydalanuvchidan matn bilan aniqlashtirishni so'raydi.
- Fuzzy-qidiruv bitta imlo xatosini yaxshi ushlaydi, lekin ikki-uch xil xato birgalikda
  bo'lsa (masalan talaffuz bo'yicha yozilgan "kamri" o'rniga "Camry") noto'g'ri model
  taklif qilishi mumkin — shu sabab bot har doim eng yaqin 2-3 variantni ham ko'rsatadi.
- Ma'lumotlar 13-May-2026 holatiga ko'ra (Yandex Pro sahifasidagi "Oxirgi yangilanish" sanasi).
  Yandex ro'yxatni yangilasa, `raw_data.txt`ni yangilab `parse.py`ni qayta ishga tushirish kerak.
