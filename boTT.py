import os
import asyncio
import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Update, FSInputFile

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.INFO)

# Проверка наличия токена
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# ========== БАЗА ДАННЫХ С ТРЕБОВАНИЯМИ ==========

MARKETING_REQUIREMENTS = """
📋 *Общие требования к маркировке (ФЗ №38, ст. 18.1, ч.16):*

• Пометка "*Реклама*" — обязательно
• "*Рекламодатель*": наименование юрлица и ИНН
• Пример: 
   *Реклама*
   *Рекламодатель: ООО ""Сияние"" (ИНН 1234567890)*
• Опционально: сайт рекламодателя
• Пометка должна быть видна в течение всего времени отображения
"""

TECH_REQUIREMENTS = {
    "olv": {
        "name": "📹 OLV (Online Video)",
        "position": "Пометка располагается в *правом верхнем углу*",
        "requirements": """
🎬 *Технические требования OLV:*

• ⏱ Хронометраж: *не более 30 секунд*
• 💾 Максимальный объем: *50 МБ*
• 📐 Разрешение: *1280x720* или *1920x1080*

*Поток:*
• 🎥 Видео битрейт: *5-7 Мбит/сек*
• 🎞 Частота кадров: *не более 25 к/сек*
• 🔊 Аудио битрейт: *80-100 кбит/сек*
• 🔇 Уровень громкости: *не более 30 дБ*
• 📊 Общий битрейт: *5-7 Мбит/сек*

*Формат:*
• 📁 Формат файла: *MP4 (MPEG-4)*
• 🎬 Видеокодек: *H.264*
• 🔊 Аудиокодек: *AAC*
"""
    },
    "display_graphic": {
        "name": "🖼 Display - Графический баннер",
        "position": "Пометка располагается в *левом верхнем углу*",
        "requirements": """
🖼 *Технические требования к графическому баннеру:*

• 💾 Максимальный вес файла: *до 150 КБ*
• 📁 Формат файла: *JPG, PNG, GIF*
• 🖌 Креатив должен иметь видимую границу

*Допустимые размеры:*
• 240×400, 728×90, 300×250, 160×600, 300×600, 320×50, 320×100, 250×250, 970×90
"""
    },
    "display_html5": {
        "name": "🎨 Display - HTML5 баннер",
        "position": "Пометка располагается в *левом верхнем углу*",
        "requirements": """
🎨 *Технические требования к HTML5 баннеру:*

• 💾 Максимальный вес: *до 150 КБ* (архив)
• 📁 Формат: *ZIP архив*
• 🖌 Креатив должен иметь видимую границу

*Содержимое архива:*
• index.html (единственный HTML-файл)
• .png, .jpg, .jpeg, .gif, .css, .js, .svg

*Обязательные требования:*
• Метатег размера в <head>
• Все файлы в одной папке
• Запрещены теги `<a>`
• Сторонний параметр для кэша: `![random]`
"""
    },
    "onctv": {
        "name": "📺 onCTV Apps",
        "position": "Пометка располагается в *правом верхнем углу*",
        "requirements": """
📺 *Технические требования onCTV Apps:*

• ⏱ Хронометраж: *не более 30 секунд*
• 💾 Максимальный объем: *50 МБ*
• 📐 Разрешение: *1280x720* или *1920x1080*

*Поток:*
• 🎥 Видео битрейт: *5-7 Мбит/сек*
• 🎞 Частота кадров: *не более 25 к/сек*
• 🔊 Аудио битрейт: *80-100 кбит/сек*

*Сейф-зона:*
• 📏 *60 пикселей сверху и снизу*
"""
    },
    "tcl_homepage_video": {
        "name": "📺 TCL - Homepage Video",
        "position": "Пометка располагается в *правом верхнем углу*",
        "requirements": """
📺 *Технические требования TCL - Homepage Video:*

• ⏱ Хронометраж: *не более 60 секунд*
• 📐 Разрешение: *1920x1080* или *1280x720*
• 🎥 Видео битрейт: *400-450 кбит/сек*
• 🎞 Частота кадров: *не более 25 к/сек*
• 🔊 Аудио битрейт: *80-100 кбит/сек*
• 📊 Общий битрейт: *480-550 кбит/сек*
• 📁 Формат: *MP4 (H.264, AAC)*
"""
    },
    "tcl_launcher_banner": {
        "name": "🖼 TCL - Launcher Banner",
        "position": "Пометка располагается в *левом верхнем углу*",
        "requirements": """
🖼 *Технические требования TCL - Launcher Banner:*

• 📁 Формат: *JPG / JPEG*
• 📐 Соотношение сторон: *16:9*
"""
    },
    "tcl_browsehere": {
        "name": "🖼 TCL - Banner in BrowseHere",
        "position": "Пометка располагается в *левом верхнем углу*",
        "requirements": """
🖼 *Технические требования TCL - Banner in BrowseHere:*

• 📁 Формат: *JPG / JPEG*
• 💾 Вес: *до 500 КБ*
• 📐 Размер: *372×210*
"""
    },
    "tcl_homepage_banner": {
        "name": "🖼 TCL - Homepage Banner",
        "position": "Пометка располагается в *левом верхнем углу*",
        "requirements": """
🖼 *Технические требования TCL - Homepage Banner:*

• 📁 Формат: *JPG / JPEG*
• 💾 Вес: *до 500 КБ*
• 📐 Размер: *982×340*
"""
    },
    "xiaomi_patchwall": {
        "name": "📺 Xiaomi - PatchWall",
        "position": "Пометка располагается в *правом верхнем углу*",
        "requirements": """
📺 *Технические требования Xiaomi - PatchWall:*

• Баннер: *640×360* (JPG, до 300 КБ)

*Задний экран:*
• Баннер: *1920×840* (JPG, до 1 МБ)
• Видео: *1920×1080*, до 30 сек, до 30 МБ (MP4, H.264, AAC)
"""
    },
    "haier_banner": {
        "name": "📺 Haier - Баннер",
        "position": "Пометка располагается в *левом верхнем углу*",
        "requirements": """
📺 *Технические требования Haier:*

• 💾 Вес: *до 5 МБ*
• 📐 Разрешение: *2136×896*
• 📁 Формат: *JPG / JPEG / PNG*
"""
    }
}

# ========== КЛАВИАТУРЫ ==========
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📹 OLV")],
        [KeyboardButton(text="🖼 Display")],
        [KeyboardButton(text="📺 onCTV Apps")],
        [KeyboardButton(text="📺 TCL")],
        [KeyboardButton(text="📺 Xiaomi")],
        [KeyboardButton(text="📺 Haier")],
        [KeyboardButton(text="ℹ️ Общие требования к маркировке")]
    ],
    resize_keyboard=True
)

display_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🖼 Графический баннер", callback_data="display_graphic"),
        InlineKeyboardButton(text="🎨 HTML5 баннер", callback_data="display_html5")
    ],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
])

tcl_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📹 Homepage Video", callback_data="tcl_homepage_video"),
        InlineKeyboardButton(text="🖼 Launcher Banner", callback_data="tcl_launcher_banner")
    ],
    [
        InlineKeyboardButton(text="🖼 Banner in BrowseHere", callback_data="tcl_browsehere"),
        InlineKeyboardButton(text="🖼 Homepage Banner", callback_data="tcl_homepage_banner")
    ],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
])

xiaomi_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📺 PatchWall", callback_data="xiaomi_patchwall")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
])

# ========== ФУНКЦИЯ ДЛЯ ОТПРАВКИ ФАЙЛА ==========
async def send_file_if_exists(message, filename, caption="📊 Технические требования в Excel"):
    file_path = f"files/{filename}"
    if os.path.exists(file_path):
        try:
            document = FSInputFile(file_path)
            await message.answer_document(document, caption=caption)
        except Exception as e:
            logging.error(f"Ошибка отправки файла {filename}: {e}")

# ========== ОБРАБОТЧИКИ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "📁 *Бот технических требований к форматам рекламы*\n\n"
        "Я помогу тебе получить технические требования для разных типов рекламных материалов.\n\n"
        "Выбери нужный формат:",
        reply_markup=main_keyboard,
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "ℹ️ Общие требования к маркировке")
async def show_marketing(message: types.Message):
    await message.answer(MARKETING_REQUIREMENTS, parse_mode="Markdown")

@dp.message(lambda message: message.text == "📹 OLV")
async def show_olv(message: types.Message):
    data = TECH_REQUIREMENTS["olv"]
    await message.answer(
        f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
        parse_mode="Markdown"
    )
    await send_file_if_exists(message, "olv.xlsx")

@dp.message(lambda message: message.text == "🖼 Display")
async def show_display_menu(message: types.Message):
    await message.answer("Выбери тип баннера:", reply_markup=display_keyboard)

@dp.message(lambda message: message.text == "📺 onCTV Apps")
async def show_onctv(message: types.Message):
    data = TECH_REQUIREMENTS["onctv"]
    await message.answer(
        f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
        parse_mode="Markdown"
    )
    await send_file_if_exists(message, "onctv.xlsx")

@dp.message(lambda message: message.text == "📺 TCL")
async def show_tcl_menu(message: types.Message):
    await message.answer("Выбери тип креатива для TCL:", reply_markup=tcl_keyboard)

@dp.message(lambda message: message.text == "📺 Xiaomi")
async def show_xiaomi_menu(message: types.Message):
    await message.answer(
        "📺 *Xiaomi*\n\nPatchWall — основной формат размещения:",
        reply_markup=xiaomi_keyboard,
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "📺 Haier")
async def show_haier(message: types.Message):
    data = TECH_REQUIREMENTS["haier_banner"]
    await message.answer(
        f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
        parse_mode="Markdown"
    )

# ========== INLINE КНОПКИ ==========
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    # Display
    if callback.data == "display_graphic":
        data = TECH_REQUIREMENTS["display_graphic"]
        await callback.message.edit_text(
            f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
            parse_mode="Markdown"
        )
        await send_file_if_exists(callback.message, "display_graphic.xlsx")
        
    elif callback.data == "display_html5":
        data = TECH_REQUIREMENTS["display_html5"]
        await callback.message.edit_text(
            f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
            parse_mode="Markdown"
        )
        await send_file_if_exists(callback.message, "display_html5.xlsx")
    
    # TCL
    elif callback.data == "tcl_homepage_video":
        data = TECH_REQUIREMENTS["tcl_homepage_video"]
        await callback.message.edit_text(
            f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
            parse_mode="Markdown"
        )
        
    elif callback.data == "tcl_launcher_banner":
        data = TECH_REQUIREMENTS["tcl_launcher_banner"]
        await callback.message.edit_text(
            f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
            parse_mode="Markdown"
        )
        
    elif callback.data == "tcl_browsehere":
        data = TECH_REQUIREMENTS["tcl_browsehere"]
        await callback.message.edit_text(
            f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
            parse_mode="Markdown"
        )
        
    elif callback.data == "tcl_homepage_banner":
        data = TECH_REQUIREMENTS["tcl_homepage_banner"]
        await callback.message.edit_text(
            f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
            parse_mode="Markdown"
        )
    
    # Xiaomi
    elif callback.data == "xiaomi_patchwall":
        data = TECH_REQUIREMENTS["xiaomi_patchwall"]
        await callback.message.edit_text(
            f"{data['requirements']}\n\n📍 *Расположение пометки:* {data['position']}",
            parse_mode="Markdown"
        )
    
    # Назад
    elif callback.data == "back_to_main":
        await callback.message.delete()
        await callback.message.answer("Выбери формат:", reply_markup=main_keyboard)
    
    await callback.answer()

# ========== ЗАПУСК НА RENDER (с веб-хуком) ==========
async def main():
    # Устанавливаем веб-хук
    await bot.set_webhook(f"{URL}/telegram", allowed_updates=["message", "callback_query"])
    
    # Создаём Starlette-приложение для обработки веб-хуков
    async def telegram_webhook(request: Request) -> Response:
        try:
            data = await request.json()
            update = Update(**data)
            await dp.feed_update(bot, update)
            return Response()
        except Exception as e:
            logging.error(f"Webhook error: {e}")
            return Response(status_code=500)
    
    async def health(request: Request) -> PlainTextResponse:
        return PlainTextResponse("OK")
    
    starlette_app = Starlette(routes=[
        Route("/telegram", telegram_webhook, methods=["POST"]),
        Route("/healthcheck", health, methods=["GET"]),
    ])
    
    # Запускаем сервер
    import uvicorn
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
