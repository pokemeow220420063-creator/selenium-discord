import asyncio
import re
from colorama import Fore, Style
from commands.handlers.action_handler import ActionHandler
from driver import Driver
from logger import Logger
from catch_statistics import CatchStatistics

logger = Logger().get_logger()
catch_statistics = CatchStatistics()

class Daily(ActionHandler):
    def __init__(self, driver: Driver):
        super().__init__(driver.bot)
        self.driver = driver

    async def start(self, command=";daily"):
        """
        Nhận thưởng hàng ngày.
        """
        logger.info(f"[Daily] Checking Daily Reward...")
        
        # 1. Gửi lệnh
        await self.driver.write(command)
        
        # 2. Đợi phản hồi
        message = await self.driver.get_last_message_from_user("PokéMeow")

        if not message:
            logger.warning("[Daily] No response from bot.")
            return

        content = (message.content or "").lower()

        # --- XỬ LÝ CÁC TRƯỜNG HỢP ---

        # Case 1: Captcha
        if "captcha" in content:
            await self.handle_action(None, message)
            return

        # Case 2: Please wait (Spam nhanh quá)
        if "please wait" in content:
            logger.info(f"[Daily] Please wait. Retrying in 4s...")
            await asyncio.sleep(4)
            await self.start(command)
            return

        # Case 3: Success (Nhận được tiền)
        if "daily reward" in content or "received" in content:
            # Regex tìm số tiền: "**12,500**" hoặc "received **12,500**"
            coins_match = re.search(r'\*\*([\d,]+)\*\*', message.content)
            coins = int(coins_match.group(1).replace(',', '')) if coins_match else 0
            
            # Masterball / Lootbox bonus?
            bonus = ""
            if "masterball" in content: bonus += " + 1 Masterball!"
            if "lootbox" in content: bonus += " + Lootbox!"

            # Thống kê
            streak_match = re.search(r'streak:\s*\*\*(\d+)\*\*', message.content, re.IGNORECASE)
            streak = streak_match.group(1) if streak_match else "?"

            logger.info(
                f"{Fore.GREEN}[Daily]{Style.RESET_ALL} "
                f"{Fore.GREEN}Claimed:{Style.RESET_ALL} {Fore.YELLOW}{coins} Coins{bonus}{Style.RESET_ALL} | "
                f"{Fore.GREEN}Streak:{Style.RESET_ALL} {Fore.CYAN}{streak}{Style.RESET_ALL}"
            )
            # Add stats (tùy chỉnh hàm add_catch hoặc tạo hàm mới trong stats)
            catch_statistics.add_catch("Daily", coins)
            return

        # Case 4: Cooldown (Chưa đến giờ)
        # Mẫu: "You can claim ... in **12H 30M**"
        elif "wait" in content and ("h" in content or "m" in content):
            time_match = re.search(r'\*\*(\d+H\s*\d+M|\d+H|\d+M|\d+S)\*\*', message.content, re.IGNORECASE)
            time_wait = time_match.group(1) if time_match else "Unknown time"

            logger.info(
                f"{Fore.GREEN}[Daily]{Style.RESET_ALL} "
                f"{Fore.GREEN}Not Ready.{Style.RESET_ALL} "
                f"{Fore.GREEN}Wait:{Style.RESET_ALL} {Fore.CYAN}{time_wait}{Style.RESET_ALL}"
            )
            return

        # Case 5: Already claimed
        elif "already claimed" in content:
             logger.info(f"[Daily] Already claimed today.")
             return