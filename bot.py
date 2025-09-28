import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatJoinRequest, Update
from aiogram.utils.executor import start_webhook
from datetime import datetime
import os
from aiohttp import web

# Твой токен и ID
API_TOKEN = "8467384823:AAFjDlnoRZHoFjImzFh_904fY5QDTZnOzaI"
OWNER_ID = 7322925570
WEBHOOK_HOST = "https://ВАШ_СЕРВИС.onrender.com"  # Замените на URL вашего Render
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

LOG_FILE = "accepted_users.json"
auto_accept = False

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загрузка логов
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        accepted_users = json.load(f)
else:
    accepted_users = []

def save_log():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(accepted_users, f, ensure_ascii=False, indent=4)

@dp.message_handler(commands=['auto_on', 'auto_off'])
async def toggle_auto_accept(message: types.Message):
    global auto_accept
    if message.from_user.id != OWNER_ID:
        await message.reply("У вас нет прав.")
        return
    auto_accept = message.text == "/auto_on"
    await message.reply(f"Автопринятие {'включено ✅' if auto_accept else 'выключено ❌'}")

@dp.message_handler(commands=['list'])
async def list_accepted(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("У вас нет прав.")
        return
    if not accepted_users:
        await message.reply("Пока никто не принят.")
    else:
        response = "\n".join([f"{u['name']} ({u['id']}) — {u['time']}" for u in accepted_users])
        await message.reply(f"Принятые пользователи:\n{response}")

@dp.chat_join_request_handler()
async def handle_join_request(join_request: ChatJoinRequest):
    global accepted_users
    if auto_accept:
        await bot.approve_chat_join_request(join_request.chat.id, join_request.from_user.id)
        accepted_users.append({
            "id": join_request.from_user.id,
            "name": join_request.from_user.full_name,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_log()

async def handle(request):
    data = await request.json()
    update = Update.to_object(data)
    await dp.process_update(update)
    return web.Response(text="ok")

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle)

if __name__ == "__main__":
    async def on_startup():
        await bot.set_webhook(WEBHOOK_URL)

    async def on_shutdown():
        await bot.delete_webhook()

    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        skip_updates=True,
        app=app
    )
