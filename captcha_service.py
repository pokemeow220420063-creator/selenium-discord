import os
import requests
import time
from datetime import datetime
from logger import Logger
from settings import Settings

logger = Logger().get_logger()
settings = Settings()

class CaptchaService:
    
    @staticmethod 
    def download_captcha(image_url):
        """
        Tải ảnh Captcha từ URL về máy.
        Hàm chạy đồng bộ (Blocking) -> Driver sẽ bọc nó trong thread.
        """
        max_attempts = 5
        timeout = 10
        
        # Tạo folder nếu chưa có
        if not os.path.exists("captchas"):
            os.makedirs("captchas")

        # Tạo tên file theo timestamp
        now = datetime.now()
        image_id = now.strftime("%d%m%Y%H%M%S%f")
        path = f"captchas/{image_id}.png"
        
        for attempt in range(max_attempts):
            try:
                # Dùng requests (Synchronous)
                response = requests.get(image_url, timeout=timeout)
                if response.status_code == 200:
                    with open(path, "wb") as file:
                        file.write(response.content)
                    return path
                else:
                    logger.error(f"[Captcha] Failed to download, code: {response.status_code}")
            except Exception as e:
                logger.error(f"[Captcha] Download attempt {attempt + 1} failed: {e}")

            time.sleep(1) # Sleep đồng bộ, OK vì chạy trong thread riêng
            
        return None

    @staticmethod 
    def send_image(image_path):
        """
        Gửi ảnh lên Server giải Captcha.
        Hàm chạy đồng bộ (Blocking).
        """
        if not image_path:
            return None

        try:
            url = settings.predict_captcha_url 
            if not url:
                logger.error("[Captcha] ❌ Predict URL not found in settings!")
                return None

            with open(image_path, "rb") as image_file:
                files = {"file": image_file}
                
                # Retry logic
                for attempt in range(5):
                    logger.info(f"🚀 Sending captcha image, attempt {attempt+1}...")
                    try:
                        # Request đồng bộ
                        response = requests.post(url, files=files, timeout=35)
                        
                        if response.status_code == 200:
                            result = response.json()
                            number = result.get("number") # Dùng .get cho an toàn
                            logger.info(f"🚀 Captcha Response: {number}")
                            return number
                        else:
                            logger.error(f"❌ API Failed, status: {response.status_code}")
                    
                    except Exception as e:
                        logger.error(f"🔌 Connection Error: {e}")
                    
                    time.sleep(5) # Đợi 5s trước khi thử lại

            return None
            
        except Exception as e:
            logger.error(f"❌ Service Exception: {e}")
            return None