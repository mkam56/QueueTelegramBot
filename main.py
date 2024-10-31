import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _

import asyncio

# Установи сюда свой API-токен
API_TOKEN = '8104732193:AAHJ_qRzjEcSu7p5Ntp-Nthy7Y7pkzbvkcs'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Список для хранения очереди
queue = []

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот, который поможет вам организовать очередь на вызов к доске.\n"
                         "Команды:\n"
                         "/add <имя> - добавить человека в очередь\n"
                         "/next - показать, кто следующий\n"
                         "/queue - показать всю очередь\n"
                         "/remove - удалить первого из очереди\n"
                         "/clear - очистить очередь")

# Команда /add для добавления в очередь
@dp.message(Command("add"))
async def add_to_queue(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        name = args[1]
        queue.append(name)
        await message.answer(f"Добавлено в очередь: {name}")
    else:
        await message.answer("Пожалуйста, укажите имя для добавления в очередь.")

# Команда /next для показа следующего
@dp.message(Command("next"))
async def show_next(message: types.Message):
    if queue:
        await message.answer(f"Следующий к доске: {queue[0]}")
    else:
        await message.answer("Очередь пустая.")

# Команда /queue для показа всей очереди
@dp.message(Command("queue"))
async def show_queue(message: types.Message):
    if queue:
        await message.answer("Очередь:\n" + "\n".join([f"{i+1}. {name}" for i, name in enumerate(queue)]))
    else:
        await message.answer("Очередь пустая.")

# Команда /remove для удаления первого из очереди
@dp.message(Command("remove"))
async def remove_from_queue(message: types.Message):
    if queue:
        removed = queue.pop(0)
        await message.answer(f"{removed} удален(а) из очереди.")
    else:
        await message.answer("Очередь пустая.")

# Команда /clear для очистки очереди
@dp.message(Command("clear"))
async def clear_queue(message: types.Message):
    queue.clear()
    await message.answer("Очередь очищена.")

# Настройка команд
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/add", description="Добавить в очередь"),
        BotCommand(command="/next", description="Следующий в очереди"),
        BotCommand(command="/queue", description="Показать очередь"),
        BotCommand(command="/remove", description="Удалить первого из очереди"),
        BotCommand(command="/clear", description="Очистить очередь")
    ]
    await bot.set_my_commands(commands)

# Запуск бота
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bot stopped!')
