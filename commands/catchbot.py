import asyncio
import re
from colorama import Fore, Style
from commands.handlers.action_handler import ActionHandler
from driver import Driver
from logger import Logger
from helpers.handle_exception import handle_on_start_exceptions
from validators.response_validator import evaluate_response
from validators.action import Action

class CatchBot(ActionHandler):
    def __init__(self, driver: Driver):
        super().__init__(driver.bot)
        self.driver = driver
        self.logger = Logger().get_logger()

    @handle_on_start_exceptions
    async def start(self, command: str = ";cb run"):
        self.logger.info(f"[CatchBot] Checking catchbot...")
        
        await self.driver.write(command)
        
        message = await self.driver.get_last_message_from_user("PokéMeow")
        if not message:
            self.logger.warning("[CatchBot] No response found.")
            return

        # Validate Captcha / Wait
        action = evaluate_response(message)
        if action == Action.SOLVE_CAPTCHA:
            await self.handle_action(Action.SOLVE_CAPTCHA, message)
            return
        
        if "please wait" in (message.content or "").lower():
            self.logger.warning(f"[CatchBot] Please wait, Retrying...")
            await asyncio.sleep(4)
            await self.start(command)
            return

        await self.process_catchbot_response(message, command)

    async def process_catchbot_response(self, message, command):
        content = (message.content or "") + " " + (message.embeds[0].description if message.embeds else "")
        full_text_lower = content.lower()

        # 1. Thu hoạch xong
        if "returned with" in full_text_lower:
            total_match = re.search(r'returned with\s+(\d+)\s+pokemon', content, re.IGNORECASE)
            total_count = total_match.group(1) if total_match else "?"
            
            # Log chi tiết (Code cũ)
            self.logger.info(f"{Fore.GREEN}[CatchBot] Finished! Total: {Fore.YELLOW}{total_count} Pokemons{Style.RESET_ALL}")
            
            # Restart
            self.logger.info(f"[CatchBot] Restarting in 5s...")
            await asyncio.sleep(5)
            await self.start(command)
            return

        # 2. Bắt đầu chạy
        elif "it will be back" in full_text_lower:
            match = re.search(r'in\s+\**([0-9HhMmSs\s]+)\**', content)
            time_wait = match.group(1).strip() if match else "Unknown"
            self.logger.info(f"{Fore.GREEN}[CatchBot] Started. Returns in: {Fore.CYAN}{time_wait}{Style.RESET_ALL}")
            return

        # 3. Đang chạy
        elif "already running" in full_text_lower:
            self.logger.info(f"[CatchBot] Already running...")
            return