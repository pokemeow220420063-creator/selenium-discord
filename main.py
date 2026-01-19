import discord
import asyncio
import os
import sys
from dotenv import load_dotenv

from settings import Settings
from driver import Driver
from bot import Bot
from logger import Logger

load_dotenv()
logger = Logger().get_logger()

# Sử dụng discord.py-self
class MySelfBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.my_bot_logic = None

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # 1. Lấy Settings
        settings = Settings()
        
        # 2. Tìm Channel object từ ID trong env
        if not settings.channel_id:
            logger.error("Vui lòng set CHANNEL_ID trong file .env!")
            await self.close()
            return
            
        target_channel = self.get_channel(settings.channel_id)
        if not target_channel:
            logger.error(f"Không tìm thấy channel có ID: {settings.channel_id}")
            # Thử fetch nếu get trả về None (ít khi cần với selfbot nhưng cứ thêm cho chắc)
            try:
                target_channel = await self.fetch_channel(settings.channel_id)
            except:
                logger.error("Không thể fetch channel.")
                await self.close()
                return

        # 3. Khởi tạo Driver (với bot=self, channel=target_channel)
        # Driver của bạn đã viết đúng async, nên truyền vào đây là chuẩn bài.
        driver = Driver(self, target_channel)
        
        # 4. Khởi tạo Bot Logic (truyền driver vào)
        self.my_bot_logic = Bot(driver)
        
        logger.info("Bot initialized. Starting Scheduler...")
        
        # 5. Chạy Scheduler (Loop chính)
        # Vì Scheduler là vòng lặp vô tận, ta await nó ở đây thì bot sẽ chạy mãi
        await self.my_bot_logic.run()

if __name__ == "__main__":
    # Check Token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in .env")
        sys.exit(1)

    # Chạy Client
    client = MySelfBot()
    client.run(token)