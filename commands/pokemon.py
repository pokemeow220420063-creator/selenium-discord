import asyncio
import re
from colorama import Fore, Style
from commands.handlers.action_handler import ActionHandler
from driver import Driver
from logger import Logger
from settings import Settings
from catch_statistics import CatchStatistics
from commands.screenshots import ScreenshotHandler
from helpers.handle_exception import handle_on_start_exceptions
from validators.response_validator import evaluate_response # Import hàm bạn đã cung cấp
from validators.action import Action

# Init Settings & Logger
settings = Settings()
logger = Logger().get_logger()
catch_statistics = CatchStatistics()

class Pokemon(ActionHandler):
    def __init__(self, driver: Driver):
        # Khởi tạo ActionHandler với bot từ driver
        super().__init__(driver.bot)
        self.driver = driver
        self.screenshot_handler = ScreenshotHandler(driver)
        
        # Load mapping bóng từ settings (Logic cũ)
        self.pokemon_ball_map = settings.pokemon_pokeball_mapping
        self.rarity_ball_map = settings.rarity_pokeball_mapping
        self.fish_ball = settings.fishing_ball
        self.shiny_ball = settings.fishing_shiny_golden_ball

    @handle_on_start_exceptions
    async def start(self, command: str = ";p"):
        """
        Hàm start chuẩn: Gửi lệnh -> Validate -> Xử lý Spawn.
        """
        logger.info("[Pokemon] Hunting a Pokemon...")
        
        # 1. Gửi lệnh
        await self.driver.write(command)
        
        # 2. Lấy tin nhắn phản hồi
        message = await self.driver.get_last_message_from_user("PokéMeow")
        
        # 3. Validate Response (Dùng hàm evaluate_response bạn đưa)
        action = evaluate_response(message)
        
        if action != Action.PROCEED:
            # Nếu không phải PROCEED thì chuyển cho Handler xử lý (Retry, Captcha, Pause, v.v.)
            # message được truyền vào để handler giải captcha nếu cần
            await self.handle_action(action, message)
            return

        # 4. Nếu Proceed -> Chuyển sang xử lý Spawn
        await self.process_pokemon_spawn(message)

    async def process_pokemon_spawn(self, message):
        """
        Logic cũ: Parse -> Log -> Chọn bóng -> Ném -> Đợi -> Kết quả
        """
        # Parse Info (Thay BeautifulSoup bằng Regex)
        info = self._parse_spawn_info(message)
        if not info:
            return # Không phải spawn message, bỏ qua

        name = info['name']
        rarity = info['rarity']
        is_shiny = info['is_shiny']
        is_golden = info['is_golden']
        
        # Log Encounter (Format cũ)
        c_color = Fore.LIGHTWHITE_EX if is_shiny else (Fore.YELLOW if is_golden else Fore.CYAN)
        logger.info(f"⚔️ {Fore.GREEN}Encountered: {c_color}{rarity} {name}{Style.RESET_ALL}")

        # Chọn bóng (Logic cũ)
        ball_to_use = self.determine_ball(name, rarity, is_shiny, is_golden)
        logger.info(f"⚾ Throwing: {Fore.YELLOW}{ball_to_use}{Style.RESET_ALL}")

        # Ném bóng (Click Button)
        await self.driver.click_on_ball(ball_to_use)

        # Đợi kết quả (Wait for Edit)
        result_message = await self.driver.wait_for_element_text_to_change(element=message, timeout=15)

        if result_message:
            # Xử lý kết quả (Logic cũ)
            await self.process_catch_result(result_message, name, rarity, is_shiny, is_golden)
        else:
            logger.warning("[Pokemon] No result message received.")

    async def process_catch_result(self, message, name, rarity, is_shiny, is_golden):
        """
        Xử lý kết quả: Caught / Broke / Ran
        """
        if not message.embeds: return
        desc = message.embeds[0].description or ""
        footer = message.embeds[0].footer.text if message.embeds[0].footer else ""

        # Case 1: Caught
        if "caught a" in desc:
            c_match = re.search(r'earned\s+(\d+)\s+PokeCoins', footer)
            coins = int(c_match.group(1)) if c_match else 0
            
            logger.info(f"✅ {Fore.GREEN}Caught {name}! {Fore.YELLOW}+{coins} Coins{Style.RESET_ALL}")
            
            # Stats
            catch_statistics.add_catch(rarity, coins)
            
            # Screenshot (Gửi Embed Log nếu là hàng xịn)
            if is_shiny or is_golden or rarity in ["Legendary", "SuperRare", "Rare"]:
                self.screenshot_handler.send_embed_log(message, rarity=rarity)

        # Case 2: Broke out
        elif "broke out" in desc:
            logger.info(f"❌ {Fore.RED}{name} broke out!{Style.RESET_ALL}")

        # Case 3: Ran away
        elif "ran away" in desc or "fled" in footer:
            logger.info(f"❌ {Fore.RED}{name} ran away!{Style.RESET_ALL}")

    def determine_ball(self, name, rarity, is_shiny, is_golden):
        """
        Logic chọn bóng (Giữ nguyên logic code cũ)
        """
        # 1. Check theo tên
        if name in self.pokemon_ball_map:
            return self.pokemon_ball_map[name]

        # 2. Check Shiny/Golden
        if is_shiny or is_golden:
            return self.shiny_ball

        # 3. Check Rarity
        ball = self.rarity_ball_map.get(rarity)
        if not ball:
            ball = self.rarity_ball_map.get(rarity.replace(" ", "")) # Handle space
        
        return ball if ball else "pokeball"

    def _parse_spawn_info(self, message):
        """
        Hàm phụ trợ parse Regex (Thay cho BS4)
        """
        if not message.embeds: return None
        embed = message.embeds[0]
        desc = embed.description or ""
        content = message.content or ""
        footer = embed.footer.text if embed.footer else ""

        # Check keyword spawn
        if "found a wild" not in content and "found a wild" not in desc:
            return None

        # Regex lấy tên
        match = re.search(r'found a wild.*?\*\*(.+?)\*\*!', content)
        if not match: match = re.search(r'found a wild.*?\*\*(.+?)\*\*!', desc)
        name = match.group(1) if match else "Unknown"

        # Regex lấy Rarity
        r_match = re.search(r'^([a-zA-Z]+)', footer)
        rarity = r_match.group(1) if r_match else "Common"

        is_shiny = "Shiny" in footer or "✨" in content or ":shiny:" in content
        is_golden = "Golden" in footer or "Golden" in name

        return {
            "name": name,
            "rarity": rarity,
            "is_shiny": is_shiny,
            "is_golden": is_golden
        }