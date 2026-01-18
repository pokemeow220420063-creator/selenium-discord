from bs4 import BeautifulSoup
from driver import Driver
from logger import Logger
from colorama import Fore, Style
import re

logger = Logger().get_logger()

class Grazz:
    @staticmethod
    def actions(driver: Driver, inventory):
        # 1. Kiểm tra số lượng
        amount = Grazz.get_grazz_amount(inventory)
        logger.info(f"[Grazz] You have {amount} Golden Razz Berries.")

        if amount > 0:
            driver.write(";grazz all")
            response = driver.get_last_element_by_user("PokéMeow", timeout=30)
            
            if response:
                text = BeautifulSoup(response.get_attribute('innerHTML'), 'html.parser').get_text(separator=" ", strip=True)

                # --- TRƯỜNG HỢP 1: THÀNH CÔNG ---
                if "ate" in text:
                    qty = re.search(r'ate\s+(\d+)x', text)
                    enc = re.search(r'for\s+(\d+)\s+encounters', text)
                    q_val = qty.group(1) if qty else "?"
                    e_val = enc.group(1) if enc else "?"
                    logger.info(f"[Grazz] Success! Used {q_val}x for {e_val} encounters.")
                
                # --- TRƯỜNG HỢP 2: LỖI / KHÁC (Log nhẹ) ---
                else:
                    logger.warning(f"[Grazz] Failed: {text[:60]}...")
            else:
                logger.warning("[Grazz] No response.")

    @staticmethod
    def get_grazz_amount(inventory) -> int:
        item = next((i for i in inventory if i['name'] == 'goldenrazzberry'), None)
        return int(item['count']) if item else 0