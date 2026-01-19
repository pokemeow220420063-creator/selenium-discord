import datetime
import os
import requests
import io
import json
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
        """
        Cách cũ: Chụp ảnh màn hình (Giữ nguyên để backup)
        """
        now = datetime.datetime.now()
        time_string = now.strftime("%I_%M_%S_%p")
        
        try:
            image_binary = element.screenshot_as_png 
            img = Image.open(io.BytesIO(image_binary))

            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            screenshots_dir = os.path.join(root_dir, 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)

            safe_rarity = rarity.replace(" ", "")
            file_name = f"{safe_rarity}_{pokemon_name}_{time_string}.png"
            screenshot_path = os.path.join(screenshots_dir, file_name)
            img.save(screenshot_path)
            
            logger.info(f"{Fore.YELLOW}[SCREENSHOT]{Style.RESET_ALL} Saved to {file_name}")
            
            # Gửi webhook kèm ảnh file
            self.send_webhook_with_image(screenshot_path, pokemon_name, rarity)
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")

    def send_webhook_with_image(self, file_path, pokemon_name, rarity):
        """Hàm phụ trợ gửi ảnh file qua webhook (Logic cũ)"""
        webhook_url = settings.webhook_url
        if not webhook_url: return

        try:
            with open(file_path, 'rb') as f:
                file_name = os.path.basename(file_path)
                payload = {
                    "embeds": [{
                        "description": f"Caught **{pokemon_name}** ({rarity})",
                        "color": 16776960, # Yellow
                        "image": {"url": f"attachment://{file_name}"},
                        "footer": {"text": "Bot by You"}
                    }]
                }
                multipart = {
                    "payload_json": (None, json.dumps(payload), "application/json"),
                    "file": (file_name, f, "image/png")
                }
                requests.post(webhook_url, files=multipart, timeout=15)
                logger.info(f'{Fore.YELLOW}[WEBHOOK]{Style.RESET_ALL} Screenshot sent!')
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    # =========================================================================
    # NEW FUNCTION: GỬI EMBED Y CHANG POKEMEOW (KHÔNG CẦN CHỤP ẢNH)
    # =========================================================================
    def send_embed_log(self, message, rarity="Unknown"):
        """
        Copy nội dung Embed từ tin nhắn của Bot và gửi qua Webhook.
        Input: message (Đối tượng discord.Message lấy từ driver)
        """
        webhook_url = settings.webhook_url
        if not webhook_url:
            logger.warning("[Screenshot] No Webhook URL provided in settings.")
            return

        if not message.embeds:
            logger.warning("[Screenshot] Message has no embeds to copy.")
            return

        # Lấy Embed gốc từ Pokemeow
        original_embed = message.embeds[0]

        try:
            # 1. Tạo Payload JSON sao chép dữ liệu
            # Lưu ý: Webhook Discord nhận dict, không nhận object discord.Embed trực tiếp
            new_embed = {
                "title": original_embed.title or f"Catch Log: {rarity}",
                "description": original_embed.description or "",
                # Lấy màu gốc hoặc mặc định màu vàng
                "color": original_embed.color.value if original_embed.color else 16776960,
                "footer": {
                    "text": f"Rarity: {rarity} | Auto-Bot Log"
                }
            }

            # Copy ảnh Pokemon (Thumbnail hoặc Image to)
            # Pokemeow thường để ảnh Pokemon ở 'image' hoặc 'thumbnail' tùy loại tin nhắn
            if original_embed.image:
                new_embed["image"] = {"url": original_embed.image.url}
            elif original_embed.thumbnail:
                new_embed["thumbnail"] = {"url": original_embed.thumbnail.url}

            # Copy các field (nếu có - ví dụ chỉ số IVs, Stats)
            if original_embed.fields:
                new_embed["fields"] = []
                for field in original_embed.fields:
                    new_embed["fields"].append({
                        "name": field.name,
                        "value": field.value,
                        "inline": field.inline
                    })

            # 2. Gửi Request
            payload = {
                "username": "PokéMeow Logger",
                "avatar_url": "https://cdn.discordapp.com/avatars/664508672713424926/0.png", # Avatar Pokemeow
                "embeds": [new_embed]
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code in [200, 204]:
                logger.info(f'{Fore.YELLOW}[WEBHOOK]{Style.RESET_ALL} {Fore.GREEN}Embed Log sent successfully!{Style.RESET_ALL}')
            else:
                logger.error(f"[WEBHOOK] Failed to send embed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"[WEBHOOK] Error copying embed: {e}")