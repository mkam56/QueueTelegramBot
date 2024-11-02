from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.filters import Command

import asyncio

# Установи сюда свой API-токен
API_TOKEN = '8104732193:AAHJ_qRzjEcSu7p5Ntp-Nthy7Y7pkzbvkcs'

# Инициализация бота и диспетчера
bot = Bot(API_TOKEN)
dp = Dispatcher()

# Список для хранения очереди
queue = []
user_last_message = {}


# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот, который поможет вам организовать очередь на вызов к доске.\n"
                         "Команды:\n"
                         "/add - добавить человека(себя) в очередь\n"
                         "/queue - показать всю очередь\n"
                         "/remove - удалить первого из очереди\n"
                         "/clear - очистить очередь, только для раба Хитори Гото")

# Команда /add для добавления в очередь
@dp.message(Command("add"))
@dp.message(Command("add"))
async def add_to_queue(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name  # Получаем полное имя пользователя

    # Удаление предыдущего сообщения, если оно существует
    if user_id in user_last_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=user_last_message[user_id])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Добавление пользователя в очередь (здесь можно реализовать логику очереди)
    queue.append(name)

    # Отправка нового сообщения и сохранение его ID
    new_message = await message.answer(f"Добавлено в очередь: {name}")
    user_last_message[user_id] = new_message.message_id

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
ADMIN_USER_ID = 1248599357  # Замените на ваш реальный user_id

@dp.message(Command("clear"))
async def clear_queue(message: types.Message):
    # Проверка, что команду использует только администратор
    if message.from_user.id == ADMIN_USER_ID:
        queue.clear()
        await message.answer("Очередь очищена.")
    else:
        await message.answer("У вас нет прав для очистки всей очереди, сосать!")

# Настройка команд
async def set_commands(botQueue: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/add", description="Добавить в очередь"),
        BotCommand(command="/queue", description="Показать очередь"),
        BotCommand(command="/remove", description="Удалить первого из очереди"),
        BotCommand(command="/clear", description="Очистить очередь")
    ]
    await botQueue.set_my_commands(commands)

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
