import json
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio


API_TOKEN = '8104732193:AAHJ_qRzjEcSu7p5Ntp-Nthy7Y7pkzbvkcs'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

QUEUE_FILE = 'queue_data.json'

queue = []

start_message_id = None
start_chat_id = None

add_priority_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Высокий приоритет", callback_data="add_low")],
    [InlineKeyboardButton(text="Средний приоритет", callback_data="add_medium")],
    [InlineKeyboardButton(text="Низкий приоритет", callback_data="add_high")],
    [InlineKeyboardButton(text="Следующий (Удалить себя)", callback_data="next_user")]
])


def load_queue():
    global queue
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, 'r') as file:
                data = file.read().strip()
                if data:
                    queue = json.loads(data)
                else:
                    queue = []
        except json.JSONDecodeError:
            print("Ошибка загрузки очереди: файл повреждён. Очередь загружается пустой.")
            queue = []
    else:
        queue = []


def save_queue():
    with open(QUEUE_FILE, 'w') as file:
        json.dump(queue, file)


def generate_queue_text():
    if queue:
        queue_list = "\n".join(
            [f"{i + 1}. {user['name']} (Приоритет: {user['priority']})" for i, user in enumerate(queue)]
        )
        text = f"Очередь:\n{queue_list}"
        if len(text) > 4000:
            text = f"Очередь:\n{queue_list[:4000]}...\n(Очередь обрезана из-за ограничений Телеграм)"
        return text
    else:
        return "Очередь пустая."


async def safe_update_start_message():
    if start_message_id and start_chat_id:
        try:
            await bot.edit_message_text(
                chat_id=start_chat_id,
                message_id=start_message_id,
                text=f"Очередь обновлена:\n\n{generate_queue_text()}",
                reply_markup=add_priority_keyboard
            )
        except Exception as e:
            print(f"Ошибка при обновлении сообщения: {e}")


async def auto_delete_message(chat_id: int, message_id: int, delay: int = 15):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    global start_message_id, start_chat_id
    start_chat_id = message.chat.id
    sent_message = await message.answer(
        "Привет! Я Хитори Гото из аниме Одинокий рокер! Я помогу вам организовать очередь.\n"
        "Выберите, пожалуйста, приоритет для добавления в очередь или нажмите 'Следующий' для удаления себя из очереди:\n"
        "Соблюдайте правила, пожалуйста, и наслаждайтесь очередью!:\n\n"
        f"{generate_queue_text()}",
        reply_markup=add_priority_keyboard
    )
    start_message_id = sent_message.message_id


async def add_to_queue_with_priority(user_id: int, name: str, priority: int):
    for user in queue:
        if user['id'] == user_id:
            temp_msg = await bot.send_message(user_id, "Вы уже находитесь в очереди.")
            asyncio.create_task(auto_delete_message(chat_id=user_id, message_id=temp_msg.message_id))
            return

    queue.append({'id': user_id, 'name': name, 'priority': priority})
    queue.sort(key=lambda x: x['priority'])
    save_queue()
    await safe_update_start_message()


@dp.callback_query(lambda c: c.data.startswith("add_"))
async def handle_add_priority_callback(callback_query: types.CallbackQuery):
    priority_map = {"add_low": 0, "add_medium": 1, "add_high": 2}
    priority = priority_map[callback_query.data]
    user_id = callback_query.from_user.id
    name = callback_query.from_user.full_name

    await add_to_queue_with_priority(user_id=user_id, name=name, priority=priority)
    await callback_query.answer()


@dp.callback_query(lambda c: c.data == "next_user")
async def handle_next_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.full_name

    for i, user in enumerate(queue):
        if user['id'] == user_id:
            queue.pop(i)
            save_queue()
            temp_msg = await callback_query.message.answer(f"{user_name} удален(а) из очереди.")
            asyncio.create_task(
                auto_delete_message(chat_id=callback_query.message.chat.id, message_id=temp_msg.message_id))
            await safe_update_start_message()
            await callback_query.answer()
            return

    temp_msg = await callback_query.message.answer("Вы не находитесь в очереди.")
    asyncio.create_task(auto_delete_message(chat_id=callback_query.message.chat.id, message_id=temp_msg.message_id))
    await callback_query.answer()


@dp.message(Command("queue"))
async def show_queue(message: types.Message):
    temp_msg = await message.answer(generate_queue_text())
    asyncio.create_task(auto_delete_message(chat_id=message.chat.id, message_id=temp_msg.message_id))


ADMIN_USER_ID = 1248599357


@dp.message(Command("clear"))
async def clear_queue(message: types.Message):
    global queue
    if message.from_user.id == ADMIN_USER_ID:
        queue.clear()
        save_queue()  # Сохранение пустой очереди после очистки
        await safe_update_start_message()
        temp_msg = await message.answer("Очередь очищена.")
    else:
        temp_msg = await message.answer("У вас нет прав для очистки всей очереди.")

    asyncio.create_task(auto_delete_message(chat_id=message.chat.id, message_id=temp_msg.message_id))


@dp.message(Command("reset"))
async def reset_queue(message: types.Message):
    global queue
    if message.from_user.id == ADMIN_USER_ID:
        queue.clear()

        try:
            with open(QUEUE_FILE, 'w') as file:
                file.write("[]")
            temp_msg = await message.answer("Очередь и сохранение успешно очищены.")
        except Exception as e:
            temp_msg = message.answer(f"Ошибка при очистке сохранения: {e}")
    else:
        temp_msg = await message.answer("У вас нет прав для очистки сохранения.")

    asyncio.create_task(auto_delete_message(chat_id=message.chat.id, message_id=temp_msg.message_id))



async def set_commands(botqueue: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/queue", description="Показать очередь"),
        BotCommand(command="/clear", description="Очистить очередь"),
        BotCommand(command="/reset", description="Очистка сохранения")
    ]
    await botqueue.set_my_commands(commands)


async def main():
    load_queue()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bot stopped!')