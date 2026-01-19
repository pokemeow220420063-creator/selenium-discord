import asyncio
import re
from colorama import Fore, Style
from commands.handlers.action_handler import ActionHandler
from driver import Driver
from logger import Logger
from catch_statistics import CatchStatistics

logger = Logger().get_logger()
catch_statistics = CatchStatistics()

class Release(ActionHandler):
    def __init__(self, driver: Driver):
        super().__init__(driver.bot)
        self.driver = driver

    async def start(self, command=";r d"):
        """
        Tự động xả (Release) Pokemon trùng lặp.
        """
        logger.info(f"[Release] Checking release duplicates...")
        
        # 1. Gửi lệnh
        await self.driver.write(command)
        
        # 2. Đợi phản hồi
        message = await self.driver.get_last_message_from_user("PokéMeow")
        
        if not message:
            logger.warning("[Release] No response from bot.")
            return

        content = (message.content or "").lower()

        # --- XỬ LÝ CAPTCHA ---
        if "captcha" in content:
            await self.handle_action(None, message)
            return

        # --- XỬ LÝ PLEASE WAIT ---
        if "please wait" in content:
            logger.info(f"[Release] Please wait. Retrying in 4s...")
            await asyncio.sleep(4)
            await self.start(command)
            return

        # --- TRƯỜNG HỢP 1: THÀNH CÔNG ---
        # Mẫu: "... released :Common:x**30** ... earning :PokeCoin: **10,600**!"
        if "released" in content and "earning" in content:
            # Parse tổng tiền
            coins_match = re.search(r'earning.*?\*\*([\d,]+)\*\*', message.content, re.IGNORECASE)
            coins = int(coins_match.group(1).replace(',', '')) if coins_match else 0
            
            # Parse chi tiết số lượng từng loại
            # Regex: :Common:x**5**
            details = re.findall(r':(\w+):x\*\*(\d+)\*\*', message.content)
            
            # Log đẹp
            rarity_config = {
                "Common": ("C", Fore.BLUE), "Uncommon": ("U", Fore.CYAN),
                "Rare": ("R", Fore.WHITE), "SuperRare": ("SR", Fore.YELLOW),
                "Legendary": ("L", Fore.MAGENTA)
            }
            
            details_list = []
            total_released = 0
            
            for rarity_name, count_str in details:
                count = int(count_str)
                total_released += count
                
                if rarity_name in rarity_config:
                    abbr, color = rarity_config[rarity_name]
                    details_list.append(f"{color}{abbr}:{count}{Style.RESET_ALL}")
                else:
                    details_list.append(f"{rarity_name}:{count}")

            detail_str = " | ".join(details_list)

            # Cập nhật thống kê
            catch_statistics.add_catch(rarity="Released Duplicates", coins=coins)

            logger.info(
                f"{Fore.GREEN}[Release]{Style.RESET_ALL} {Fore.GREEN}Success!{Style.RESET_ALL} "
                f"{Fore.GREEN}Total:{Style.RESET_ALL} {Fore.CYAN}{total_released}{Style.RESET_ALL} ({detail_str}) | "
                f"{Fore.GREEN}Earned:{Style.RESET_ALL} {Fore.YELLOW}{coins} Coins{Style.RESET_ALL}"
            )
            return

        # --- TRƯỜNG HỢP 2: KHÔNG CÓ GÌ ĐỂ RELEASE ---
        elif "don't have any duplicate" in content:
            logger.info(f"[Release] No duplicates to release.")
            return