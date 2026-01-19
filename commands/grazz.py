import asyncio
import re
from logger import Logger
from colorama import Fore, Style

logger = Logger().get_logger()

class Grazz:
    @staticmethod
    async def actions(driver, inventory):
        """
        Tự động bật Golden Razz Berry (Grazz) nếu có.
        """
        # 1. Tìm item 'golden razz berry' trong inventory
        # Tên item có thể là 'golden razz berry' hoặc 'goldenrazzberry' tùy cách parse
        grazz_count = next((item['count'] for item in inventory if 'golden' in item['name'].lower() and 'razz' in item['name'].lower()), 0)
        
        logger.info(f"[Grazz] You have {grazz_count} Golden Razz Berries.")

        if grazz_count > 0:
            # Gửi lệnh
            await driver.write(";grazz all")
            
            # Đợi phản hồi
            await asyncio.sleep(2)
            message = await driver.get_last_message_from_user("PokéMeow")

            if not message:
                logger.warning("[Grazz] No response from bot.")
                return

            content = message.content or ""

            # --- TRƯỜNG HỢP 1: THÀNH CÔNG ---
            # Dựa vào code cũ, từ khóa là "ate"
            # Giả định mẫu: "You fed **1x**... Pokemon ate it... for **X** encounters"
            if "ate" in content or "fed" in content:
                # Regex tìm số lượng (thường là **1**x)
                qty_match = re.search(r'\*\*(\d+)x?\*\*', content)
                # Regex tìm số encounter
                enc_match = re.search(r'for\s+(\d+)\s+encounters', content) # Code cũ không có **, check linh hoạt
                if not enc_match:
                     enc_match = re.search(r'for\s+\*\*(\d+)\*\*\s+encounters', content) # Check có **

                q_val = qty_match.group(1) if qty_match else "?"
                e_val = enc_match.group(1) if enc_match else "?"

                logger.info(f"{Fore.GREEN}[Grazz] Success! Used {q_val}x for {e_val} encounters.{Style.RESET_ALL}")

            # --- TRƯỜNG HỢP 2: THẤT BẠI ---
            # Mẫu JSON bạn gửi: ":x: You don't have a :goldenrazzberry:!..."
            elif "You don't have" in content:
                 logger.warning(f"[Grazz] Failed: Not enough Golden Razz Berries.")
            
            # --- TRƯỜNG HỢP KHÁC ---
            else:
                logger.info(f"[Grazz] Unknown response: {content[:50]}...")