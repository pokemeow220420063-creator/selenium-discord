from bs4 import BeautifulSoup
from driver import Driver
from logger import Logger
from colorama import Fore, Style
import re

logger = Logger().get_logger()

class Repel:
    @staticmethod
    def actions(driver: Driver, inventory):
        # 1. Kiểm tra số lượng
        amount = Repel.get_repel_amount(inventory)
        logger.info(f"[Repel] You have {amount} Repels.")

        if amount > 0:
            driver.write(";repel all")
            response = driver.get_last_element_by_user("PokéMeow", timeout=30)
            
            if response:
                text = BeautifulSoup(response.get_attribute('innerHTML'), 'html.parser').get_text(separator=" ", strip=True)

                # --- TRƯỜNG HỢP 1: THÀNH CÔNG ---
                if "activated" in text:
                    qty = re.search(r'activated\s+(\d+)x', text)
                    enc = re.search(r'for\s+(\d+)\s+encounters', text)
                    q_val = qty.group(1) if qty else "?"
                    e_val = enc.group(1) if enc else "?"
                    logger.info(f"[Repel] Success! Activated {q_val}x for {e_val} encounters.")
                
                # --- TRƯỜNG HỢP 2: LỖI / KHÁC (Log nhẹ) ---
                else:
                    logger.warning(f"[Repel] Failed: {text[:60]}...")
            else:
                logger.warning("[Repel] No response.")

    @staticmethod
    def get_repel_amount(inventory) -> int:
        item = next((i for i in inventory if i['name'] == 'repel'), None)
        return int(item['count']) if item else 0