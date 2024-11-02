import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher
from comands import main_router


bot = Bot(token=getenv('BOT_TOKEN'))

# Запуск бота
async def main():
    try:
        dp = Dispatcher()
        dp.include_router(main_router)

        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bot stopped!')

