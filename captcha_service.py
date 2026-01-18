import os
import requests
import time
from datetime import datetime
from logger import Logger
from settings import Settings  # Gọi "Ví tổng" đã tạo

logger = Logger().get_logger()
settings = Settings()          # Lấy dữ liệu đã nạp sẵn từ settings.py

class CaptchaService:
    
    @staticmethod 
    def download_captcha(href):
        image_url = href
        max_attempts = 5
        timeout = 10
        if not os.path.exists("captchas"):
            os.makedirs("captchas")

        now = datetime.now()
        image_id = now.strftime("%d%m%Y%H%M%S%f")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(image_url, timeout=timeout)
                if response.status_code == 200:
                    path = f"captchas/{image_id}.png"
                    with open(path, "wb") as file:
                        file.write(response.content)
                    return path
                else:
                    logger.error(f"Failed to download, code: {response.status_code}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")

            time.sleep(1)
        return None

    @staticmethod 
    def send_image(image_path):
        try:
            # --- LẤY URL TỪ SETTINGS ---
            url = settings.predict_captcha_url 

            with open(image_path, "rb") as image_file:
                files = {"file": image_file}
                retry_delay = 5
                for attempt in range(5):
                    logger.info(f"🚀 Sending image, attempt {attempt+1}...")
                    try:
                        response = requests.post(url, files=files, timeout=35)
                        if response.status_code == 200:
                            logger.info("🚀 Image sent successfully!")
                            return response.json()["number"]
                        else:
                            logger.error(f"❌ Failed, status: {response.status_code}")
                    except Exception as e:
                        logger.error(f"🔌 Error: {e}")
                    
                    time.sleep(retry_delay)

            return None
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return None