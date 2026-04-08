from aiogram import Bot, Dispatcher
import os
import asyncio
from dotenv import load_dotenv
from conspector import consp_router
from ai_gpt import ai_router
import asyncio

load_dotenv()
TOKEN = os.getenv('k_token')
bot = Bot(token=TOKEN) 

dp = Dispatcher()
async def main():
    dp.include_router(consp_router)
    dp.include_router(ai_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
       asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
