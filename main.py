import json
import os
from collections import Counter


from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import cast
import asyncio
import random
from dotenv import load_dotenv


load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

QUEUE_FILE = "queue_data.json"

QUEUE_SAVE_FILE = "queue_state.json"

queue = []

sanctions = []

start_message_id = None
start_chat_id = None

queue_message_id = None
queue_chat_id = None

print("Введите название предмета - которое должно совпадать с названием в таблице!")
sub = str(input())

add_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Добавить себя в очередь", callback_data="add")],
        [
            InlineKeyboardButton(
                text="Удалить себя из очереди", callback_data="next_user"
            )
        ],
    ]
)


def load_classmates():
    if not os.path.exists(QUEUE_FILE):
        print("Файл не найден. Создаётся пустой список.")
        return []

    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as file:
            data = file.read().strip()
            if not data:
                print("Файл пуст. Возвращается пустой список.")
                return []

            return json.loads(data)
    except json.JSONDecodeError:
        print("Ошибка: файл содержит некорректный JSON.")
        return []
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return []


def save_classmates(classmate_list):
    with open(QUEUE_FILE, "w") as file:
        json.dump(classmate_list, cast([str], file), indent=4)


def generate_queue_text():
    if queue:
        queue_list = "\n".join(
            [f"{i + 1}. {user['name']}" for i, user in enumerate(queue)]
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
                text="Привет! Я Хитори Гото из аниме "
                "Одинокий рокер"
                "! Я помогу вам организовать очередь.\n"
                "Нажмите, пожалуйста, кнопку "
                "добавить себя"
                " чтобы поучаствовать в очереди :\n"
                "После того как все желающие запишутся под этим сообщением, создастся очередь основанная на ваших баллах :\n"
                "Соблюдайте правила, пожалуйста, и наслаждайтесь очередью! :\n\n"
                f"{generate_queue_text()}",
                reply_markup=add_keyboard,
            )
        except Exception as e:
            print(f"Ошибка при обновлении сообщения: {e}")


async def auto_delete_message(chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        if "message to delete not found" in str(e):
            print(f"Сообщение {message_id} уже удалено.")
        else:
            print(f"Ошибка при удалении сообщения: {e}")


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        temp_msg = await message.answer("Пошел нахуй!")
        sanctions.append(temp_msg.username)
        await asyncio.create_task(
            auto_delete_message(
                chat_id=temp_msg.chat.id, message_id=temp_msg.message_id, delay=15
            )
        )
        return
    else:
        global start_message_id, start_chat_id
        start_chat_id = message.chat.id
        sent_message = await message.answer(
            "Привет! Я Хитори Гото из аниме "
            "Одинокий рокер"
            "! Я помогу вам организовать очередь.\n"
            "Нажмите, пожалуйста, кнопку "
            "добавить себя"
            " чтобы поучаствовать в очереди :\n"
            "После того как все желающие запишутся под этим сообщением, создастся очередь основанная на ваших баллах :\n"
            "Соблюдайте правила, пожалуйста, и наслаждайтесь очередью! :\n\n"
            f"{generate_queue_text()}",
            reply_markup=add_keyboard,
        )
        start_message_id = sent_message.message_id


async def add_to_queue_with_priority(user_id: int, name: str, username: str = None):
    global classmates

    for user in queue:
        if user["id"] == user_id:
            temp_msg = await bot.send_message(
                user_id, "Вы уже находитесь в очереди. Привет, как дела? Как жизнь?"
            )
            await asyncio.create_task(
                auto_delete_message(
                    chat_id=user_id, message_id=temp_msg.message_id, delay=15
                )
            )
            return

    queue.append({"id": user_id, "name": name})

    existing_user = next((u for u in classmates if u["id"] == user_id), None)

    if not existing_user:
        new_user = {
            "id": user_id,
            "name": name,
            "telegram_username": username or "",
            "grades": {
                "math_line": 0,
                "math_anal": 0,
                "computer architecture": 0,
                "skkv": 0,
            },
        }
        classmates.append(new_user)
        save_classmates(classmates)

    await safe_update_start_message()


@dp.callback_query(lambda c: c.data.startswith("add"))
async def handle_add_priority_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()

    user_id = callback_query.from_user.id
    name = callback_query.from_user.full_name
    username = callback_query.from_user.username

    await add_to_queue_with_priority(user_id=user_id, name=name, username=username)


@dp.callback_query(lambda c: c.data == "next_user")
async def handle_next_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()

    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.full_name

    for i, user in enumerate(queue):
        if user["id"] == user_id:
            queue.pop(i)
            temp_msg = await callback_query.message.answer(
                f"{user_name} удален(а) из очереди."
            )
            await asyncio.create_task(
                auto_delete_message(
                    chat_id=callback_query.message.chat.id,
                    message_id=temp_msg.message_id,
                    delay=15,
                )
            )
            await safe_update_start_message()
            return

    temp_msg = await callback_query.message.answer("Вы не находитесь в очереди.")
    await asyncio.create_task(
        auto_delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=temp_msg.message_id,
            delay=15,
        )
    )


classmates = load_classmates()


async def generate_queue():
    global queue

    if not queue:
        return "Очередь пустая."

    queue_with_grades = []
    for user in queue:
        user_data = next((x for x in classmates if x["id"] == user["id"]), None)
        grades_sum = int(
            user_data["grades"][sub].values()
            if user_data and "grades" in user_data
            else 0
        )

        queue_with_grades.append({**user, "grades_sum": grades_sum})

    queue_with_grades.sort(key=lambda x: (x["grades_sum"], random.random()))

    queue = queue_with_grades

    queue_text = "\n".join(
        f"{i + 1}. {user['name']} — {user['grades_sum']} баллов"
        for i, user in enumerate(queue)
    )

    return f"Очередь:\n{queue_text}"


async def safe_update_queue_message():
    global queue_message_id, queue_chat_id

    if queue_message_id and queue_chat_id:
        try:
            updated_queue_text = generate_queue_text()
            await bot.edit_message_text(
                chat_id=queue_chat_id,
                message_id=queue_message_id,
                text=updated_queue_text,
            )
        except Exception as e:
            print(f"Ошибка при обновлении сообщения с очередью: {e}")


@dp.message(Command("done"))
async def analyse(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        temp_msg = await message.answer("Пошел нахуй!")
        await asyncio.create_task(
            auto_delete_message(
                chat_id=temp_msg.chat.id, message_id=temp_msg.message_id, delay=15
            )
        )
        return

    global start_message_id, start_chat_id
    await auto_delete_message(
        chat_id=start_chat_id or 0, message_id=start_message_id or 0, delay=0
    )

    global queue_message_id, queue_chat_id
    queue_chat_id = message.chat.id

    try:
        generated_queue = await generate_queue()
        send_message = await message.answer(generated_queue)
        queue_message_id = send_message.message_id
    except Exception as e:
        print(f"Ошибка при генерации очереди: {e}")


@dp.message(Command("remove"))
async def remove(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        temp_msg = await message.answer("Пошел нахуй!")
        await asyncio.create_task(
            auto_delete_message(
                chat_id=temp_msg.chat.id, message_id=temp_msg.message_id, delay=15
            )
        )
        return

    global queue, sub
    if not queue:
        await message.answer("Очередь пуста.")
        return

    try:
        removed_user = queue.pop(0)

        await safe_update_queue_message()

        for classmate in classmates:
            if classmate["id"] == removed_user["id"]:
                classmate["grades"][sub] = classmate["grades"].get(sub, 0) + 2.5
                break

        save_classmates(classmates)

        temp = await message.answer(
            f"Пользователь {removed_user['name']} был удален из очереди и получил +2.5 баллов приоритета."
        )
        await auto_delete_message(temp.chat.id, temp.message_id, delay=15)
    except Exception as e:
        print(f"Ошибка при удалении: {e}")


def save_queue():
    with open(QUEUE_SAVE_FILE, "w", encoding="utf-8") as file:
        json.dump(queue, cast([str], file), indent=4, ensure_ascii=False)


def load_queue():
    global queue
    if os.path.exists(QUEUE_SAVE_FILE):
        try:
            with open(QUEUE_SAVE_FILE, "r", encoding="utf-8") as file:
                queue = json.load(file)
        except json.JSONDecodeError:
            print("Ошибка при загрузке очереди: некорректный JSON.")
            queue = []
    else:
        queue = []


@dp.message(Command("start"))
async def start_command(message: types.Message):
    load_queue()
    await message.answer("Очередь загружена из файла.")
    await safe_update_queue_message()


@dp.message(Command("late_join"))
async def add_late_user(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name

    if any(user["id"] == user_id for user in queue):
        await message.answer("Вы уже в очереди!")
        return

    existing_user = next((u for u in classmates if u["id"] == user_id), None)
    priority = sum(existing_user["grades"].values()) if existing_user else 0

    queue.append({"id": user_id, "name": name, "grades_sum": priority})
    save_queue()

    await safe_update_queue_message()
    await message.answer("Вы добавлены в конец очереди с учетом приоритета.")


@dp.message(Command("switch"))
async def switch_places(message: types.Message):
    user_id = message.from_user.id
    if not any(user["id"] == user_id for user in queue):
        await message.answer("Вы не в очереди!")
        return

    switch_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Поменяться местами", callback_data=f"switch_{user_id}"
                )
            ]
        ]
    )

    await message.answer(
        "Кто хочет поменяться местами? Нажмите кнопку ниже:", reply_markup=switch_button
    )


@dp.callback_query(lambda c: c.data.startswith("switch_"))
async def handle_switch_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    target_id = int(callback_query.data.split("_")[1])

    if user_id == target_id:
        await callback_query.answer("Нельзя поменяться с самим собой.", show_alert=True)
        return

    user_idx = next((i for i, user in enumerate(queue) if user["id"] == user_id), None)
    target_idx = next(
        (i for i, user in enumerate(queue) if user["id"] == target_id), None
    )

    if user_idx is None or target_idx is None:
        await callback_query.answer(
            "Один из участников больше не в очереди.", show_alert=True
        )
        return

    queue[user_idx], queue[target_idx] = queue[target_idx], queue[user_idx]
    save_queue()
    await safe_update_queue_message()
    await callback_query.message.answer("Вы успешно поменялись местами!")


@dp.message(Command("test_distribution"))
async def test_distribution(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("У вас нет прав для выполнения этой команды!")
        return

    test_queue = [
        {"id": 1, "name": "Иван Иванов"},
        {"id": 2, "name": "Мария Петрова"},
        {"id": 3, "name": "Алексей Смирнов"},
        {"id": 4, "name": "Альфа"},
        {"id": 5, "name": "Бета"},
        {"id": 6, "name": "Гамма"},
    ]
    global queue
    queue = test_queue

    position_counts = Counter()

    for _ in range(1000):
        generated_queue = await generate_queue()
        names_order = [
            line.split(" — ")[0].split(". ")[1]
            for line in generated_queue.split("\n")[1:]
        ]
        for position, name in enumerate(names_order, start=1):
            position_counts[(name, position)] += 1

    result = "Распределение:\n\n"
    for (name, position), count in position_counts.items():
        result += f"{name} на месте {position}: {count} раз\n"

    await message.answer(result)


def create_commands():
    return []


async def set_commands(bot_queue: Bot):
    await bot_queue.set_my_commands(create_commands())


async def main():

    await set_commands(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")
