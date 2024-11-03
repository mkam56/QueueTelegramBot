import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis import Redis
from comands import main_router


# redis.acl_setuser(username=getenv("REDIS_USER", default=""), password=getenv("REDIS_USER_PASSWORD", default=""))


# Запуск бота
async def main():
    try:
        # storage = RedisStorage(Redis(
        #     host=getenv("REDIS_HOST", default="localhost"),
        #     port=getenv("REDIS_PORT", default=6379),
        #     db=getenv("REDIS_DB", default=0),
        #     password=getenv("REDIS_PASSWORD", default=""),
        # ))

        storage = MemoryStorage()

        dp = Dispatcher(storage=storage)

        bot = Bot(token=getenv('BOT_TOKEN'))

        dp.include_router(main_router)

        await bot.delete_webhook(drop_pending_updates=True) # пропускаем все накопленные сообщения.
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bot stopped!')

