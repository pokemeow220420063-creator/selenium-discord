import time
import re
from colorama import Fore, Style
from logger import Logger

class Send:
    def __init__(self, driver, settings):
        self.driver = driver
        self.logger = Logger().get_logger()
        self.settings = settings  # Đã có settings từ lúc khởi tạo class

    def start(self):
        # 1. LẤY ID TRỰC TIẾP TỪ SETTINGS (Không mở file config nữa)
        send_id = self.settings.send_id
        
        # --- VALIDATE ID ---
        if not send_id:
            self.logger.error(f"{Fore.RED}[Send] 'send_id' not found in settings!{Style.RESET_ALL}")
            return

        receiver_id = str(send_id).strip()
        
        # Logic: Phải là số và độ dài từ 17-20 ký tự
        if not receiver_id.isdigit() or not (17 <= len(receiver_id) <= 20):
            self.logger.error(f"{Fore.RED}[Send] Invalid Discord ID!{Style.RESET_ALL}")
            self.logger.info(f"[Send] Current ID: '{receiver_id}' (Length: {len(receiver_id)})")
            self.logger.warning("[Send] Action cancelled. Returning to bot...")
            return
        # -------------------

        self.logger.info(f"{Fore.YELLOW}[Send] Execution paused...{Style.RESET_ALL}")
        
        # 2. Check Balance
        self.logger.info('[Send] Checking balance ...')
        self.driver.write(";coins")
        time.sleep(3) 

        # 3. Read Balance from Embed
        current_coins = "Unknown"
        try:
            element = self.driver.get_last_element_by_user("PokéMeow")
            if element:
                text_content = element.text
                match = re.search(r'([\d,]+)\s+PokeCoins', text_content)
                
                if match:
                    current_coins = match.group(1)
                else:
                    self.logger.info(f"[Send] Could not read exact balance.")
        except Exception as e:
            self.logger.warning(f"[Send] Error reading balance: {e}")

        # 4. User Input
        print("="*40)
        print(f"{Fore.YELLOW}[Send] RECEIVER: {receiver_id}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[Send] BALANCE:  {current_coins}{Style.RESET_ALL}")
        print("="*40)
        
        try:
            # Nhập số tiền muốn chuyển
            amount = input(f"{Fore.GREEN}[Send] Enter amount to give (Press Enter to cancel): {Style.RESET_ALL}").strip()
        except Exception:
            amount = ""

        # 5. Execute Give Command
        if amount:
            # Xử lý nếu người dùng nhập có dấu phẩy (ví dụ: 1,000,000)
            amount_clean = amount.replace(',', '')
            
            if amount_clean.isdigit():
                command = f";give {receiver_id} {amount_clean}"
                self.logger.info(f"[Send] Sending command: {Fore.GREEN}{command}{Style.RESET_ALL}")
                self.driver.write(command)
                
                time.sleep(2)
                self.logger.info(f"{Fore.GREEN}[Send] Transaction command sent!{Style.RESET_ALL}")
            else:
                self.logger.warning(f"{Fore.YELLOW}[Send] Invalid amount: '{amount}'{Style.RESET_ALL}")
        else:
            self.logger.info(f"{Fore.GREEN}[Send] Transaction cancelled.{Style.RESET_ALL}")

        print("="*40 + "\n")
        self.logger.warning('[Send] Resuming Bot...')