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

class Release(ActionHandler):
    def __init__(self, driver: Driver):
        super().__init__()
        self.driver = driver
        self.logger = Logger().get_logger()

    @handle_on_start_exceptions
    def start(self, command: str = ";r d"):
        self.logger.info(f"[Release] Checking release...")
        self.driver.write(command)
        
        element_response = self.driver.get_last_element_by_user("PokéMeow", timeout=15)
        
        # --- XỬ LÝ PLEASE WAIT ---
        if "Please wait" in element_response.text:
            self.logger.warning(f"[Release] Please wait. Retrying...")
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

        self.process_release_response(element_response)

    def process_release_response(self, element):
        soup = BeautifulSoup(element.get_attribute('outerHTML'), "html.parser")
        
        # 1. Xóa phần trích dẫn (Reply)
        for reply in soup.find_all(class_=re.compile("repliedMessage")):
            reply.decompose()

        # 2. Thay thế hình ảnh bằng text (alt) để Regex bắt được độ hiếm
        for img in soup.find_all("img", alt=True):
            img.replace_with(img['alt'])

        # 3. Lấy text sạch
        full_text = soup.get_text(separator=' ', strip=True)
        full_text = re.sub(r'\s+', ' ', full_text) # Xóa khoảng trắng thừa
        full_text_lower = full_text.lower()

        # --- LOGIC XỬ LÝ ---

        # 1. TRƯỜNG HỢP THÀNH CÔNG
        if "released" in full_text_lower and "earning" in full_text_lower:
            
            # Lấy chi tiết các loại đã thả (Tìm chuỗi kiểu ":Rare: x 3")
            details = re.findall(r':(\w+):\s*x\s*(\d+)', full_text)
            
            # Lấy số Coins
            coins_match = re.search(r'earning.*?([\d,]+)', full_text, re.IGNORECASE)
            coins = coins_match.group(1) if coins_match else "0"
            
            # Tính tổng số lượng
            total_released = sum(int(count) for _, count in details)
            
            # Cấu hình màu sắc
            rarity_config = {
                "Common":    ("C", Fore.BLUE),
                "Uncommon":  ("U", Fore.CYAN),
                "Rare":      ("R", Fore.WHITE),     # Giả lập cam bằng đỏ
                "SuperRare": ("SR", Fore.YELLOW),
                "Legendary": ("L", Fore.MAGENTA),
                "Shiny":     ("S", Fore.LIGHTWHITE_EX)
            }
            
            # Tạo chuỗi log có màu
            formatted_parts = []
            for name, count in details:
                if name in rarity_config:
                    abbr, color = rarity_config[name]
                    # Format: {MÀU}{VIẾT TẮT}:{SỐ}{RESET}
                    formatted_parts.append(f"{color}{abbr}:{count}{Style.RESET_ALL}")
                else:
                    formatted_parts.append(f"{name}:{count}")
            
            detail_str = " | ".join(formatted_parts)

            self.logger.info(
                f"{Fore.GREEN}[Release]{Style.RESET_ALL} {Fore.GREEN}Success!{Style.RESET_ALL} "
                f"{Fore.GREEN}Total:{Style.RESET_ALL} {Fore.CYAN}{total_released}{Style.RESET_ALL} ({detail_str}) | "
                f"{Fore.GREEN}Earned:{Style.RESET_ALL} {Fore.YELLOW}{coins} Coins{Style.RESET_ALL}"
            )
            return

        # 2. TRƯỜNG HỢP KHÔNG CÓ GÌ ĐỂ RELEASE
        elif "don't have any duplicate" in full_text_lower:
            self.logger.info(f"[Release] No duplicate Pokemon to release.")
            return

        # 3. TRƯỜNG HỢP KHÁC
        else:
            self.logger.warning(f"[Release] Unknown response: {full_text[:60]}...")