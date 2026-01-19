import asyncio
import re
from logger import Logger
from catch_statistics import CatchStatistics

logger = Logger().get_logger()
catch_statistics = CatchStatistics()

class Lootbox:
    @staticmethod
    async def actions(driver, inventory):
        """
        Tự động mở Lootbox nếu số lượng >= 10.
        """
        # 1. Kiểm tra số lượng
        amount = Lootbox.get_lootbox_amount(inventory)
        logger.info(f"[Lootbox] You have {amount} lootboxes...")

        if amount >= 10:
            logger.info(f"[Lootbox] Opening {amount} lootboxes...")
            
            # Gửi lệnh
            await driver.write(";lb all")
            
            # Đợi phản hồi
            response = await driver.get_last_element_by_user("PokéMeow", timeout=30)
            
            if response is None:
                logger.warning("[Lootbox] Failed to get response (Timeout).")
                return

            # 2. Parse items bằng Regex
            items = Lootbox.extract_items(response.content)
            
            # 3. Log và Thống kê
            if items:
                logger.info(f"[Lootbox] Items Earned:")
                
                # Cập nhật thống kê
                catch_statistics.add_lootboxes_opened(amount)
                
                for name, qty in items.items():
                    catch_statistics.add_item_lootbox(name, qty)
                    logger.info(f"[Lootbox] {name}: {qty}")
            else:
                logger.warning("[Lootbox] Opened but found no items (Parsing failed?).")
                
    @staticmethod
    def get_lootbox_amount(inventory) -> int:
        # Tìm item có tên 'lootbox' trong inventory list
        return next((item['count'] for item in inventory if item['name'] == 'lootbox'), 0)
    
    @staticmethod
    def extract_items(content):
        """
        Regex parse text từ tin nhắn Lootbox.
        """
        items = {}
        if not content: return items

        # 1. Bắt item thường: "**6 x** :pokeball:"
        item_matches = re.findall(r'\*\*([\d,]+)\s*x\*\*\s*:([a-zA-Z0-9_]+):', content)
        for qty_str, name in item_matches:
            try:
                items[name] = int(qty_str.replace(',', ''))
            except ValueError: continue

        # 2. Bắt PokeCoin: ":PokeCoin: **1,439**!"
        coin_match = re.search(r':PokeCoin:\s*\*\*([\d,]+)\*\*', content)
        if coin_match:
            try:
                items['pokecoin'] = int(coin_match.group(1).replace(',', ''))
            except ValueError: pass

        return items