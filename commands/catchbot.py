from bs4 import BeautifulSoup
from commands.handlers.action_handler import ActionHandler
from driver import Driver
from logger import Logger
from helpers.handle_exception import handle_on_start_exceptions
from helpers.sleep_helper import interruptible_sleep
from validators.response_validator import evaluate_response
from validators.action import Action
from colorama import Fore, Style
import re

class CatchBot(ActionHandler):
    def __init__(self, driver: Driver):
        super().__init__()
        self.driver = driver
        self.logger = Logger().get_logger()

    @handle_on_start_exceptions
    def start(self, command: str = ";cb run"):
        self.logger.info(f"[CatchBot] Checking catchbot...")
        self.driver.write(command)
        
        element_response = self.driver.get_last_element_by_user("PokéMeow", timeout=15)
        # Retry logic
        if "Please wait" in element_response.text:
            self.logger.warning(f"[CatchBot] Please wait, Retrying...")
            interruptible_sleep(4)
            return self.start(command)

        # Validate
        action = evaluate_response(element_response)
        if action is Action.SKIP:
            interruptible_sleep(2)
            return
        if action is not Action.PROCEED:
            self.handle_action(action, self.driver, element_response)
            return

        self.process_catchbot_response(element_response, command)

    def process_catchbot_response(self, element, command):
        soup = BeautifulSoup(element.get_attribute('outerHTML'), "html.parser")
        
        # 1. Xóa phần trích dẫn (Reply)
        for reply in soup.find_all(class_=re.compile("repliedMessage")):
            reply.decompose()

        # 2. MẸO: Thay thế hình ảnh bằng tên của nó để dễ đọc
        # Ví dụ: <img alt=":Common:"> sẽ thành text ":Common:"
        # Điều này giúp ta đọc được dòng ":Common: x01 | :Rare: x00"
        for img in soup.find_all("img", alt=True):
            img.replace_with(img['alt'])

        # 3. Lấy text sạch sau khi đã thay thế ảnh
        full_text = soup.get_text(separator=' ', strip=True)
        full_text_lower = full_text.lower()

        # --- LOGIC XỬ LÝ ---

        # 1. Thu hoạch xong (Returned)
        if "returned with" in full_text_lower:
            # Lấy tổng số lượng
            total_match = re.search(r'returned with\s+(\d+)\s+pokemon', full_text, re.IGNORECASE)
            total_count = total_match.group(1) if total_match else "?"
            
            # Lấy chi tiết từng loại (C, UC, R, SR, L, S)
            # Regex tìm chuỗi kiểu ":Common: x01" hoặc ":Rare: x05"
            details = re.findall(r':(\w+):\s*x(\d+)', full_text)
            
            # Map tên đầy đủ sang viết tắt cho gọn log
            rarity_config = {
                "Common":    ("C", Fore.BLUE),
                "Uncommon":  ("U", Fore.CYAN),
                "Rare":      ("R", Fore.WHITE),     # Colorama không có Orange, dùng Red thay thế
                "SuperRare": ("SR", Fore.YELLOW),
                "Legendary": ("L", Fore.MAGENTA)
            }
            
            # Tạo chuỗi hiển thị có màu (VD: XanhC:1 | ĐỏR:2)
            formatted_parts = []
            for name, count in details:
                if name in rarity_config:
                    abbr, color = rarity_config[name]
                    # Format: {MÀU}{TÊN}:{SỐ}{RESET}
                    formatted_parts.append(f"{color}{abbr}:{count}{Style.RESET_ALL}")
                else:
                    # Nếu có loại lạ (Event...) thì để mặc định
                    formatted_parts.append(f"{name}:{count}")

            detail_str = " | ".join(formatted_parts)
            
            # Log ra màn hình
            self.logger.info(
                f"{Fore.GREEN}[CatchBot]{Style.RESET_ALL} "
                f"{Fore.GREEN}Finished! Total: {Fore.YELLOW}{total_count} Pokemons{Fore.GREEN} "
                f"({detail_str}{Fore.GREEN}){Style.RESET_ALL}"
            )
            
            # Restart
            self.logger.info(f"[CatchBot] Restarting in 5s...")
            interruptible_sleep(5)
            self.start(command)
            return

        # 2. Bắt đầu chạy (Sent / Mission started)
        elif "it will be back" in full_text_lower:
            # Regex bắt thời gian: "in 1H ." -> Lấy "1H"
            match = re.search(r'in\s+([0-9HhMmSs\s]+)(?:\.|$)', full_text)
            time_wait = match.group(1).strip() if match else "Unknown"
            
            self.logger.info(f"{Fore.GREEN}[CatchBot] Started. Returns in:{Style.RESET_ALL} {Fore.CYAN}{time_wait}{Style.RESET_ALL}")
            return

        # 3. Đang chạy rồi
        elif "already running" in full_text_lower:
            self.logger.info(f"[CatchBot] Already running...")
            return

        # 4. Hết tiền
        elif "don't have enough money" in full_text_lower or "insufficient funds" in full_text_lower:
            self.logger.warning(f"[CatchBot] Not enough money!")
            return
        elif "please vote to claim your loot" in full_text_lower:
            self.logger.warning(f"[CatchBot] Please vote to claim your loot.")
            return

        # 5. Unknown
        else:
            self.logger.warning(f"[CatchBot] Unknown response: {full_text[:60]}...")