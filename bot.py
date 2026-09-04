import asyncio
import json
import logging
import os
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from core import search_model, format_result, extract_model_from_ocr_text

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

OWNER_FILE = os.path.join(os.path.dirname(__file__), "owner.json")


def get_owner_id() -> int | None:
    if not os.path.exists(OWNER_FILE):
        return None
    try:
        with open(OWNER_FILE, encoding="utf-8") as f:
            return json.load(f).get("owner_id")
    except (json.JSONDecodeError, OSError):
        return None


def set_owner_id(user_id: int) -> None:
    with open(OWNER_FILE, "w", encoding="utf-8") as f:
        json.dump({"owner_id": user_id}, f)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    owner_id = get_owner_id()
    if owner_id is None:
        set_owner_id(message.from_user.id)
        await message.answer(
            "👑 Tabriklaymiz! Siz botni birinchi bo'lib ishga tushirdingiz va endi "
            "<b>bot egasi (owner)</b> deb belgilandingiz.\n\n",
            parse_mode="HTML",
        )
    elif owner_id == message.from_user.id:
        await message.answer("👑 Xush kelibsiz, Owner!\n\n", parse_mode="HTML")

    await message.answer(
        "Salom! Men Yandex Taxi (Toshkent) tarif-mos keluvchi botman.\n\n"
        "🔤 Menga avtomobil markasi va modelini yozing (masalan: <i>BYD Yuan Up</i>)\n"
        "📷 Yoki texnik pasport rasmini yuboring — men modelni o'qishga harakat qilaman.\n\n"
        "Men qaysi tariflarga (Start / Standart / Komfort / Electro / Komfort+ / Biznes / Premier) "
        "mos kelishini va qaysi yildan ekanini aytib beraman.",
        parse_mode="HTML",
    )


@dp.message(F.photo)
async def photo_handler(message: Message):
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        await message.answer(
            "OCR kutubxonalari o'rnatilmagan. Iltimos, mashina nomini matn ko'rinishida yuboring."
        )
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    buf = BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    buf.seek(0)

    await message.answer("🔎 Rasmni o'qiyapman...")

    img = Image.open(buf)
    text = pytesseract.image_to_string(img, lang="uzb+rus+eng")

    candidate = extract_model_from_ocr_text(text)
    if not candidate:
        await message.answer(
            "Kechirasiz, rasmdan model nomini aniq o'qiy olmadim. "
            "Iltimos, mashina markasi va modelini matn qilib yozib yuboring "
            "(masalan: <i>BYD Yuan Up</i>).",
            parse_mode="HTML",
        )
        return

    matches = search_model(candidate)
    if not matches:
        await message.answer(
            f"Rasmdan «<b>{candidate}</b>» deb o'qidim, lekin ro'yxatda mos model topilmadi. "
            f"To'g'ri nomini yozib yuborasizmi?",
            parse_mode="HTML",
        )
        return

    best_model, score = matches[0]
    await message.answer(
        f"Rasmdan «<b>{candidate}</b>» deb o'qidim.\n"
        f"Eng yaqin topilgan: <b>{best_model}</b> (moslik: {score:.0f}%)\n\n"
        + format_result(best_model),
        parse_mode="HTML",
    )
    if len(matches) > 1:
        alt = ", ".join(m for m, _ in matches[1:])
        await message.answer(f"Boshqa yaqin variantlar: {alt}")


@dp.message(F.text)
async def text_handler(message: Message):
    query = message.text.strip()
    matches = search_model(query)

    if not matches:
        await message.answer(
            "Bunday model ro'yxatda topilmadi. Nomni to'g'riroq yozib ko'ring "
            "(masalan: <i>BYD Yuan Up</i>, <i>Chevrolet Cobalt</i>, <i>Toyota Camry</i>).",
            parse_mode="HTML",
        )
        return

    best_model, score = matches[0]
    if score == 100 or len(matches) == 1:
        await message.answer(format_result(best_model), parse_mode="HTML")
    else:
        await message.answer(
            f"Eng yaqin topilgan: <b>{best_model}</b> (moslik: {score:.0f}%)\n\n"
            + format_result(best_model),
            parse_mode="HTML",
        )
        alt = ", ".join(m for m, _ in matches[1:] if m != best_model)
        if alt:
            await message.answer(f"Boshqa yaqin variantlar: {alt}")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
