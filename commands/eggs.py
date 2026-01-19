import asyncio
import re
from logger import Logger
from colorama import Fore, Style
from catch_statistics import CatchStatistics

from logger import Logger
logger = Logger().get_logger()
class Egg:
    @staticmethod
    async def actions(driver, inventory):
        """
        Refactor: Chuyển sang Async.
        Logic:
        1. Lấy tin nhắn Inventory vừa xuất hiện.
        2. Soi trạng thái trứng (Ready/Counter/Empty).
        3. Hatch hoặc Hold tùy tình huống.
        """
        logger.info("[Egg] Checking Eggs status...")
        
        # 1. Lấy tin nhắn cuối cùng (Tin nhắn Inventory)
        # Vì hàm check_inventory vừa chạy xong, tin nhắn cuối chính là nó.
        message = await driver.get_last_message_from_user("PokéMeow")
        
        if not message:
            logger.info("[Egg] Could not find inventory message.")
            return

        # 2. Phân tích trạng thái từ Embed Inventory
        egg_status = Egg.get_egg_status(message)
        can_hold_egg = False

        # 3. Logic Ấp trứng (Hatch)
        if egg_status["can_hatch"]:
            await asyncio.sleep(3)
            logger.info(f"{Fore.YELLOW}🐣 Hatching egg...{Style.RESET_ALL}")
            
            # Gửi lệnh ấp
            await driver.write(";egg hatch")
            can_hold_egg = True # Nở xong thì tay rảnh
            
            # Đợi tin nhắn kết quả nở trứng
            hatch_msg = await driver.get_last_element_by_user("PokéMeow", timeout=30)
            await asyncio.sleep(6)
            
            if hatch_msg:
                # Lấy tên Pokemon nở ra
                pokemon_hatched = Egg.get_hatch_result(hatch_msg)
                
                if pokemon_hatched:
                    if catch_statistics:
                        catch_statistics.add_hatch(pokemon_hatched)
                    logger.info(f"🐣{Fore.GREEN} A {Style.RESET_ALL}{Fore.LIGHTCYAN_EX}{pokemon_hatched}{Style.RESET_ALL} {Fore.GREEN}has been hatched!{Style.RESET_ALL}")

        # 4. Logic Cầm trứng (Hold)
        # Kiểm tra xem có trứng trong túi đồ không
        poke_egg_count = next((item['count'] for item in inventory if item['name'] == 'poke_egg'), 0)
        
        if poke_egg_count > 0:
            # Nếu Inventory báo rảnh tay HOẶC vừa mới ấp xong
            if egg_status["can_hold"] or can_hold_egg:
                logger.info(f"{Fore.YELLOW}🥚 Holding egg...{Style.RESET_ALL}")
                await driver.write(";egg hold")
                await asyncio.sleep(2.5)

    @staticmethod
    def get_egg_status(message):
        """
        Refactor: Thay thế BeautifulSoup.
        Soi Embed của tin nhắn ;inv để tìm chuỗi [COUNTER: ...] hoặc [READY TO HATCH!]
        """
        status = {"can_hatch": False, "can_hold": True} # Mặc định là hold được nếu không tìm thấy gì
        
        if not message or not message.embeds:
            return status

        # Duyệt qua các field trong Embed Inventory
        # Thông thường thông tin trứng nằm ở field "Fishing" hoặc "Eggs" tùy version bot
        for field in message.embeds[0].fields:
            value = field.value
            
            # Case 1: Trứng đã chín
            if "[READY TO HATCH!]" in value:
                return {"can_hatch": True, "can_hold": False}
            
            # Case 2: Đang ấp dở (Có Counter)
            if "[COUNTER:" in value:
                return {"can_hatch": False, "can_hold": False}
            
            # Case 3: Không tìm thấy 2 chuỗi trên trong field này -> Tiếp tục vòng lặp
        
        # Nếu duyệt hết mà không thấy Counter/Ready -> Tức là chưa cầm trứng
        return status

    @staticmethod
    def get_hatch_result(message):
        """
        Refactor: Dùng Regex bắt tên Pokemon từ tin nhắn kết quả ấp trứng.
        Mẫu: "You just hatched a **Pikachu**!"
        """
        if not message.embeds:
            return None
            
        description = message.embeds[0].description or ""
        
        # Regex tìm chuỗi trong **...** sau cụm từ "hatched a"
        match = re.search(r'hatched a \*\*(.+?)\*\*', description)
        
        if match:
            return match.group(1)
            
        return None