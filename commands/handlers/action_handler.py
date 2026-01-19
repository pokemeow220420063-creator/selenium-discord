import asyncio
import random
from validators.action import Action
from logger import Logger
from catch_statistics import CatchStatistics
from captcha_service import CaptchaService 

logger = Logger().get_logger()
catch_statistics = CatchStatistics()
captcha_service = CaptchaService()

class ActionHandler:
    def __init__(self, bot):
        self.bot = bot
        self.action_handlers = {
            Action.RETRY: self.retry,
            Action.SOLVE_CAPTCHA: self.solve_captcha,
            Action.PAUSE: self.pause,
            Action.CATCH_AGAIN: self.catch_again,
            Action.SKIP: self.skip,
            Action.REFRESH: self.refresh # Vẫn xử lý Action Refresh
        }
        self.command = None
    
    # Hàm này không còn raise NotImplementedError nữa mà điều phối thật
    async def handle_action(self, action, message=None):
        handler = self.action_handlers.get(action)
        if not handler: return

        # Nếu là giải Captcha, cần truyền message để lấy ảnh
        if action == Action.SOLVE_CAPTCHA:
            await handler(message)
        else:
            await handler()

    async def retry(self):
        # Logic cũ có sleep 1.5s ở validator, giờ đưa vào đây
        await asyncio.sleep(1.5)
        # start(command) cũ -> Logic loop bên ngoài sẽ tự gửi lại lệnh
        pass

    async def refresh(self):
        # API không F5 được, nhưng vì Validator trả về REFRESH khi mất mạng
        # Nên ta xử lý giống Retry
        await asyncio.sleep(2)
        pass

    async def catch_again(self):
        # Logic cũ sleep 3s
        await asyncio.sleep(3)
        pass
        
    async def skip(self):
        # Logic cũ raise NotImplemented, nhưng API thì cứ bỏ qua để chạy tiếp
        pass

    async def pause(self):
        catch_statistics.print_statistics()
        # Logic cũ input(""), API không chặn được nên dùng wait
        logger.warning("Bot paused via Action.PAUSE")
        await asyncio.sleep(86400) # Ngủ 1 ngày giả lập dừng bot

    async def solve_captcha(self, message):
        """
        Logic giải Captcha mới (tải ảnh -> gửi API) 
        nhưng dùng LOG y hệt logic cũ bạn cung cấp
        """
        
        # 1. Lấy Link Ảnh (Logic mới cần thiết cho API)
        image_url = None
        if message.attachments: image_url = message.attachments[0].url
        elif message.embeds and message.embeds[0].image: image_url = message.embeds[0].image.url
            
        if not image_url:
            logger.error("Captcha number is None. Trying again...") # Log cũ
            return

        # 2. Tải và Gửi ảnh (Dùng thread để không đơ bot)
        catch_statistics.add_captcha_encounter()
        
        # Giả lập logic: number = self.get_captcha()
        img_path = await asyncio.to_thread(captcha_service.download_captcha, image_url)
        number = await asyncio.to_thread(captcha_service.send_image, img_path)
        
        if number is None:
            # Log y hệt code cũ
            logger.error("Captcha number is None. Trying again...")
            await asyncio.sleep(3)
            # Thử lại (đệ quy hoặc return để loop chính xử lý)
            return
        
        # 3. Gửi kết quả
        # Log y hệt code cũ
        logger.info(f"🔢 Captcha response: {number}")
        await asyncio.sleep(random.randint(10, 15)) 
        logger.info("Submitting captcha response...")
        
        await message.channel.send(str(number))
        
        # 4. Kiểm tra kết quả (Thay cho wait_for_element_text_to_change)
        def check(m):
            return m.author.id == message.author.id and m.channel.id == message.channel.id

        try:
            response_msg = await self.bot.wait_for('message', check=check, timeout=120)
            
            if "Thank you" in response_msg.content:
                # Log y hệt code cũ
                logger.warning('Captcha solved, continuing...')
            else:
                # Log y hệt code cũ
                logger.error('Captcha failed, trying again!')
                # self.solve_captcha(new_element) -> Logic đệ quy API
                
        except asyncio.TimeoutError:
            logger.error('Captcha failed, trying again!') # Timeout cũng coi như fail