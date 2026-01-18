import datetime
import os
import requests
import io
import json # <--- Cần thêm thư viện này
from colorama import Fore, Style
from PIL import Image
from logger import Logger
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from settings import Settings

logger = Logger().get_logger()
settings = Settings()

class ScreenshotHandler:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def take_screenshot_by_element(self, element: WebElement, pokemon_name: str, rarity: str = "Legendary"):
        now = datetime.datetime.now()
        time_string = now.strftime("%I_%M_%S_%p")
        
        try:
            # Chụp ảnh element
            image_binary = element.screenshot_as_png 
            img = Image.open(io.BytesIO(image_binary))

            # Lưu file
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            screenshots_dir = os.path.join(root_dir, 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)

            safe_rarity = rarity.replace(" ", "")
            file_name = f"{safe_rarity}_{pokemon_name}_{time_string}.png"
            screenshot_path = os.path.join(screenshots_dir, file_name)
            img.save(screenshot_path)
            
            logger.info(f'{Fore.YELLOW}[SCREENSHOT]{Style.RESET_ALL} {Fore.YELLOW}Screenshot saved: {screenshot_path}{Style.RESET_ALL}')

            # Gửi Webhook
            self.send_to_webhook(pokemon_name, screenshot_path, rarity)

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")

    def send_to_webhook(self, pokemon_name, file_path, rarity):
        webhook_url = settings.webhook_url
        if not webhook_url:
            return

        session_name = os.getenv('SESSION_NAME', 'Bot')
        file_name = os.path.basename(file_path)

        # 1. CẤU HÌNH EMOJI
        emoji_map = {
            "Legendary": "<:Legendary:667123969245184022>",
            "Shiny": "<:Shiny:667126233217105931>",
            "Golden": "<:Golden:676623920711073793>"
        }
        key = rarity.title()
        emoji = emoji_map.get(key, "")

        # 2. CẤU HÌNH MÀU SẮC (Discord dùng hệ số nguyên Int, không dùng Hex String trực tiếp)
        # Cách đổi: int("MãHex", 16)
        color_map = {
            "Legendary": 0xa007f8,  # Tím đậm theo yêu cầu
            "Shiny": 0xff99cc,      # Hồng phấn theo yêu cầu
            "Golden": 0xffffcc,     # Light Yellow (Vàng nhạt)
            "Super Rare": 0x00ffff, # Cyan (Dự phòng)
            "Rare": 0xff0000        # Red (Dự phòng)
        }
        # Lấy màu, mặc định là trắng nếu không tìm thấy
        embed_color = color_map.get(rarity, 0xffffff)

        # Nội dung hiển thị (Header)
        content_text = f"{emoji} **{pokemon_name}** catch by **{session_name}**"

        try:
            with open(file_path, 'rb') as f:
                # 3. TẠO PAYLOAD JSON EMBED
                payload = {
                    "embeds": [
                        {
                            "description": content_text,  # Dòng chữ sẽ nằm trong khung
                            "color": embed_color,         # Màu viền
                            "image": {
                                "url": f"attachment://{file_name}" # Mẹo: Trỏ vào file đang upload
                            },
                            "footer": {
                                "text": f"Rarity: {rarity}"
                            }
                        }
                    ]
                }

                # 4. GỬI REQUEST MULTIPART (Vừa file, vừa JSON)
                # 'payload_json' là field đặc biệt của Discord để nhận JSON kèm file
                multipart_data = {
                    "payload_json": (None, json.dumps(payload), "application/json"),
                    "file": (file_name, f, "image/png")
                }

                requests.post(webhook_url, files=multipart_data, timeout=15)
                logger.info(f'{Fore.YELLOW}[WEBHOOK]{Style.RESET_ALL} {Fore.MAGENTA}Embed Screenshot sent!{Style.RESET_ALL}')
                
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")