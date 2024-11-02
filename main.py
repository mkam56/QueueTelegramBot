from queue import Queue

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
import asyncio

# Установи сюда свой API-токен
API_TOKEN = '8104732193:AAHJ_qRzjEcSu7p5Ntp-Nthy7Y7pkzbvkcs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Очередь, где каждый элемент — словарь с данными пользователя и приоритетом
queue = []

# Словарь для хранения ID последнего сообщения для каждого пользователя
user_last_message = {}

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я товарищ Майор, который поможет вам организовать очередь вызова на фронт.\n"
                         "Команды:\n"
                         "/add <приоритет(чудо яйца) от 0 до 2>- добавить человека(себя) в очередь с определённым приоритетом\n"
                         "/queue - показать всю очередь\n"
                         "/next - удалить первого из очереди и показать следующего\n"
                         "/clear - очистить очередь, только для раба Хитори Гото")

# Команда /add для добавления пользователя с приоритетом
@dp.message(Command("add"))
async def add_to_queue(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name  # Получаем полное имя пользователя
    args = message.text.split(maxsplit=1)

    # Проверка наличия приоритета
    if len(args) < 2 or not args[1].isdigit() or not (0 <= int(args[1]) <= 2):
        await message.answer("Пожалуйста, укажите приоритет (0, 1 или 2) после команды /add.")
        return

    priority = int(args[1])

    # Проверка, чтобы пользователь не добавлялся дважды
    for user in queue:
        if user['id'] == user_id:
            await message.answer("Вы уже находитесь в очереди.")
            return

    # Удаление предыдущего сообщения, если оно существует
    if user_id in user_last_message:
        try:
            await bot.delete_message(chat_id=user_id, message_id=user_last_message[user_id])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Добавление пользователя в очередь с сортировкой по приоритету
    queue.append({'id': user_id, 'name': name, 'priority': priority})
    queue.sort(key=lambda x: x['priority'])

    # Отправка сообщения и сохранение ID
    new_message = await message.answer(f"Добавлено в очередь: {name} с приоритетом {priority}")
    user_last_message[user_id] = new_message.message_id


# Команда /queue для показа всей очереди
@dp.message(Command("queue"))
async def show_queue(message: types.Message):
    if queue:
        queue_list = "\n".join(
            [f"{i + 1}. {user['name']} (Приоритет: {user['priority']})" for i, user in enumerate(queue)])
        await message.answer(f"Очередь:\n{queue_list}")
    else:
        await message.answer("Очередь пустая.")

# Команда /next для показа и удаления следующего пользователя
@dp.message(Command("next"))
async def show_next(message: types.Message):
    if queue.__len__() > 1:
        remove = queue.pop(0)
        next_user = queue[-1]
        await message.answer(f"Следующий к доске: {next_user['name']} (Приоритет: {next_user['priority']})")
    else:
        await message.answer("Очередь пустая.")


# Команда /clear с проверкой прав администратора
ADMIN_USER_ID = 1248599357  # Замените на ваш реальный user_id


@dp.message(Command("clear"))
async def clear_queue(message: types.Message):
    if message.from_user.id == ADMIN_USER_ID:
        queue.clear()
        await message.answer("Очередь очищена.")
    else:
        await message.answer("У вас нет прав для очистки всей очереди.")

# Настройка команд
async def set_commands(botQueue: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/add", description="Добавить в очередь"),
        BotCommand(command="/next", description="Удалить и показать следующего"),
        BotCommand(command="/queue", description="Показать очередь"),
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
