import asyncio
import re
from logger import Logger
from colorama import Fore, Style

logger = Logger().get_logger()

class Repel:
    @staticmethod
    async def actions(driver, inventory):
        """
        Tự động bật Repel nếu có trong túi.
        """
        # 1. Tìm item 'repel' trong inventory
        # Lưu ý: tên trong inv thường là 'repel' (chữ thường)
        repel_count = next((item['count'] for item in inventory if 'repel' in item['name'].lower()), 0)
        
        logger.info(f"[Repel] You have {repel_count} Repels.")

        if repel_count > 0:
            # Gửi lệnh
            await driver.write(";repel all")
            
            # Đợi phản hồi (Repel thường phản hồi nhanh)
            await asyncio.sleep(2)
            message = await driver.get_last_message_from_user("PokéMeow")

            if not message:
                logger.warning("[Repel] No response from bot.")
                return

            content = message.content or ""

            # --- TRƯỜNG HỢP 1: THÀNH CÔNG ---
            # Mẫu JSON: "You activated **1x** :repel: **Repel**... for **30** encounters!"
            if "activated" in content:
                # Regex tìm số trong **...** hoặc số đứng sau chữ activated/for
                # Tìm số lượng repel đã dùng
                qty_match = re.search(r'activated\s+\*\*(\d+)x?\*\*', content)
                # Tìm số encounter
                enc_match = re.search(r'for\s+\*\*(\d+)\*\*\s+encounters', content)

                q_val = qty_match.group(1) if qty_match else "?"
                e_val = enc_match.group(1) if enc_match else "?"
                
                logger.info(f"{Fore.GREEN}[Repel] Success! Activated {q_val}x for {e_val} encounters.{Style.RESET_ALL}")

            # --- TRƯỜNG HỢP 2: THẤT BẠI (Hết hàng dù check inv thấy có - đề phòng sync lỗi) ---
            # Mẫu JSON: ":x: You don't have a :repel:!"
            elif "You don't have" in content:
                logger.warning(f"[Repel] Failed: Not enough repels (Server said no).")
            
            # --- TRƯỜNG HỢP KHÁC ---
            else:
                # In ra đoạn đầu tin nhắn để debug nếu có mẫu câu lạ
                logger.info(f"[Repel] Unknown response: {content[:50]}...")