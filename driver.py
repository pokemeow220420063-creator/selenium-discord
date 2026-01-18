import configparser
import json
import os
import random
import time
import requests
from email.utils import parsedate_to_datetime
import datetime
import chromedriver_autoinstaller
import colorama
from colorama import Fore, Back, Style
from dotenv import load_dotenv
import pyotp
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    SessionNotCreatedException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from captcha_service import CaptchaService
from catch_statistics import CatchStatistics
from commands.shop import Shop
from helpers.sleep_helper import interruptible_sleep
from logger import Logger
from settings import Settings
load_dotenv()
config = configparser.ConfigParser()
settings = Settings()
    
catch_statistics = CatchStatistics()


ENABLE_AUTO_BUY_BALLS = os.getenv('ENABLE_AUTO_BUY_BALLS') == 'True'
ENABLE_RELEASE_DUPLICATES = os.getenv('ENABLE_RELEASE_DUPLICATES') == 'True'
ENABLE_AUTO_EGG_HATCH = os.getenv('ENABLE_AUTO_EGG_HATCH') == 'True'
ENABLE_AUTO_LOOTBOX = os.getenv('ENABLE_AUTO_LOOTBOX_OPEN') == 'True'
ENABLE_FISHING = os.getenv('ENABLE_FISHING') == 'True'
ENABLE_BATTLE_NPC = os.getenv('ENABLE_BATTLE_NPC') == 'True'
ENABLE_HUNTING = os.getenv('ENABLE_HUNTING') == 'True'
ENABLE_AUTO_QUEST_REROLL = os.getenv('ENABLE_AUTO_QUEST_REROLL') == 'True'
ENABLE_RUN_PICTURES = os.getenv('ENABLE_RUN_PICTURES') == 'True'
ENABLE_CHROME_HEADLESS = os.getenv('ENABLE_CHROME_HEADLESS') == 'True'

logger = Logger().get_logger()
captcha_service = CaptchaService()

# Get the JSON string from the .ini
pokeball_for_pokemon = settings.pokemon_pokeball_mapping
rarity_pokeball_mapping = settings.rarity_pokeball_mapping
rarity_emoji = settings.rarity_emoji
fishing_ball = settings.fishing_ball
hunt_item_ball = settings.hunt_item_ball
fish_shiny_golden_ball = settings.fishing_shiny_golden_ball



class Driver:
    def __init__(self, driver_path):
        # Instance logger
        
        load_dotenv()
        self.driver_path = driver_path
        self.driver = None
        
    def start_driver(self):
        # Set up Chrome options
        options = Options()
        options.add_argument("--log-level=3")
        #Open the browser 1000x1000
        options.add_argument("--window-size=1000,1000")
        # Disable notifications
        options.add_argument("--disable-notifications")
        # Disable infobars
        options.add_argument("--disable-infobars")
        
        #make the driver lightweight
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--mute-audio")
        
        options.headless = ENABLE_CHROME_HEADLESS

        try:
            self.driver = webdriver.Chrome(executable_path=self.driver_path, options=options)
            
        except SessionNotCreatedException:
            logger.error("Error: The version of ChromeDriver is not compatible with your installed version of Google Chrome.")
            logger.error("Please update Google Chrome to the latest version or install a compatible version of ChromeDriver.")
            raise  # re-raise the exception after handling it
        except:
            logger.warning(f"Driver not found in path: {self.driver_path}")
            logger.warning(f"or version incompatible")
            logger.warning(f"Downloading compatible version...")
            chromedriver_autoinstaller.install()
            self.driver = webdriver.Chrome(options=options)
    
    def navigate_to_page(self, url):
        if self.driver is not None:
            self.driver.get(url)
        else:
            logger.info("Driver not started. Call start_driver first.")

    def quit_driver(self):
        if self.driver is not None:
            self.driver.quit()
        else:
            logger.info("Driver not started. Nothing to quit.")
            
    def inject_token(self, token) -> bool:
        logger.info("Loging with token!")
        # Open Discord login page
        self.driver.get("https://discord.com/login")

        # Inject token using JavaScript
        script = f"""
            const token = "{token}";
            setInterval(() => {{
                document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"${{token}}"`;
            }}, 50);
            setTimeout(() => {{
                location.reload();
            }}, 2500);
        """
        self.driver.execute_script(script)

        # Wait for the login process to complete
        # Wait for the URL to match 'https://discord.com/channels/@me'
        WebDriverWait(self.driver, 15).until(lambda d: d.current_url == 'https://discord.com/channels/@me')

        # Verify if login was successful (you can add your own logic here)
        if self.driver.current_url == "https://discord.com/channels/@me":
            logger.info("Login successful!")
            logger.info("Login successful!")
            logger.info("Login successful!")
            return True
        else:
            logger.error("Login with token failed.")
            logger.error("Login with token failed.")
            logger.error("Login with token failed.")
            return False
        
    def login(self, email, password):
        """
        Hàm đăng nhập Discord hỗ trợ tự động nhập 2FA và chờ giải Captcha thủ công.
        Yêu cầu: 
        - Biến auth_secret phải được định nghĩa chính xác từ Discord 2FA Setup.
        - Đã cài đặt thư viện pyotp (pip install pyotp)
        - Đảm bảo giờ hệ thống (Windows/Linux) đã được đồng bộ chuẩn xác.
        """

        # CHỈ SỬA ĐOẠN NÀY: Lấy secret từ môi trường và làm sạch chuỗi
        # Ưu tiên lấy từ file .bat (AUTHENTICATOR_SECRET), nếu không có mới lấy mặc định
        env_secret = os.getenv('AUTHENTICATOR_SECRET')
        if env_secret:
            authenticator_secret = env_secret.replace(" ", "").strip().upper()
        else:
            # Giá trị dự phòng nếu không tìm thấy biến môi trường
            raw_secret = getattr(self, 'auth_secret', "lrp52ecakdrynehvhhsnkeimygh7fqaq")
            authenticator_secret = raw_secret.replace(" ", "").strip().upper()

        logger.info("Đang tiến hành đăng nhập bằng Email và Password...")

        for attempt in range(3):
            try:
                # Tải trang đăng nhập nếu chưa có
                if "login" not in self.driver.current_url:
                    self.driver.get("https://discord.com/login")
                
                # Đợi và nhập Email
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'email'))
                )
                email_field.send_keys(Keys.CONTROL + 'a')
                email_field.send_keys(Keys.DELETE)
                time.sleep(0.5)
                email_field.send_keys(email)

                # Nhập Password
                password_field = self.driver.find_element(By.NAME, 'password')
                password_field.send_keys(Keys.CONTROL + 'a')
                password_field.send_keys(Keys.DELETE)
                time.sleep(0.5)
                password_field.send_keys(password)

                # Click nút Đăng nhập
                time.sleep(random.randint(1, 3))
                self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
                
                logger.info("Đã gửi thông tin. Đang kiểm tra bước tiếp theo (Captcha hoặc 2FA)...")

                # Vòng lặp kiểm tra trạng thái sau khi nhấn nút Login
                login_success = False
                mfa_sent = False 

                for i in range(60): # Chờ tối đa khoảng 120 giây
                    current_url = self.driver.current_url
                    
                    # TH 1: Đã vào được trang chủ
                    if 'https://discord.com/channels/@me' in current_url:
                        logger.info('Đăng nhập thành công!')
                        login_success = True
                        break

                    # TH 2: Kiểm tra xem có ô nhập 2FA không
                    mfa_inputs = self.driver.find_elements(By.XPATH, "//input[@autocomplete='one-time-code'] | //input[contains(@class, 'inputDefault')]")
                    
                    if mfa_inputs and ('login' in current_url or 'mfa' in current_url):
                        if not mfa_sent:
                            logger.info("Phát hiện yêu cầu 2FA. Đang tạo mã...")
                            try:
                                # Sử dụng secret đã được làm sạch ở trên
                                # --- SỬA ĐỔI: Lấy giờ chuẩn từ Google thay vì giờ máy tính ---
                                # --- SỬA ĐỔI: Lấy giờ chuẩn từ Google (Đã fix lỗi xung đột tên biến) ---
                                try:
                                    # Gửi request nhẹ đến Google để lấy Header thời gian
                                    response = requests.head("https://www.google.com", timeout=5)
                                    server_time_str = response.headers['Date']
                                    
                                    # Dùng hàm đã import trực tiếp, không gọi qua 'email.' nữa
                                    parsed_time = parsedate_to_datetime(server_time_str)
                                    
                                    # Đảm bảo dùng múi giờ UTC để tính toán
                                    current_timestamp = parsed_time.timestamp()                                    
                                    # Tạo mã dựa trên timestamp của Google
                                    totp = pyotp.TOTP(authenticator_secret)
                                    code = totp.at(current_timestamp)

                                except Exception as time_err:
                                    logger.warning(f"Không lấy được giờ Internet ({time_err}), dùng giờ máy tính.")
                                    # Fallback: Dùng giờ hệ thống nếu mất mạng hoặc lỗi
                                    totp = pyotp.TOTP(authenticator_secret)
                                    code = totp.now()

                                input_2fa = mfa_inputs[0]
                                # Kết hợp clear và xóa thủ công để đảm bảo ô nhập trống rỗng
                                input_2fa.clear()
                                input_2fa.send_keys(Keys.CONTROL + 'a')
                                input_2fa.send_keys(Keys.DELETE)
                                time.sleep(0.3)
                                
                                # Gửi mã kèm dấu xuống dòng (\n) để kích hoạt sự kiện submit của Discord
                                input_2fa.send_keys(code + "\n") 
                                
                                logger.info(f"Mã 2FA tạo ra: {code}. Đã nhập và đợi xác nhận...")
                                mfa_sent = True 
                                time.sleep(5)
                                continue
                            except Exception as mfa_err:
                                logger.error(f"2FA step failed: {mfa_err}")
                                mfa_sent = False 
                        else:
                            # Nếu mã đã gửi nhưng vẫn ở trang 2FA sau 20s, cho phép nhập lại mã mới
                            if i % 10 == 0: 
                                mfa_sent = False
                                logger.info("Chuẩn bị thử lại mã 2FA mới...")
                    
                    else:
                        # TH 3: Không phải trang chủ, cũng không thấy ô 2FA -> Có thể là Captcha
                        if not mfa_sent:
                            logger.info("Đang đợi giải Captcha hoặc chờ màn hình 2FA xuất hiện...")
                        else:
                            pass

                    time.sleep(2)

                if login_success:
                    return True
                else:
                    raise Exception("Hết thời gian chờ. Đăng nhập thất bại.")

            except Exception as e:
                logger.error(f'Lần thử {attempt + 1} thất bại: {str(e)}')
                if attempt == 2:
                    logger.error('Tất cả các lần thử đăng nhập đều thất bại')
                    return False
                time.sleep(3)
        
        return False
                
    def write(self, msg):
        # span = self.driver.find_element(By.XPATH, "//span[contains(@class='emptyText'])")
        span = self.driver.find_element(By.XPATH, "//span[contains(@class, 'emptyText')]")

        ActionChains(self.driver).send_keys_to_element(span, Keys.BACK_SPACE*20).send_keys_to_element(span, msg).perform()
        ActionChains(self.driver).send_keys_to_element(span, Keys.ENTER).perform()
    
    def click_next_button(self):
        try:
            # Wait until the 'Next' buttons are present (timeout after 10 seconds)
            wait = WebDriverWait(self.driver, 10)
            next_buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'img[alt="arrow_forward"]')))

            # Select the last 'Next' button from the list
            if next_buttons:
                last_button = next_buttons[-1]
                # Scroll the last element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", last_button)

                # Additional wait to handle dynamic content such as pop-ups or notifications
                time.sleep(1)  # Adjust sleep time based on observed behavior of the web page

                # Perform the click using ActionChains for better precision
                ActionChains(self.driver).move_to_element(last_button).click().perform()
                return True  # Return True indicating the action was successfully completed
            else:
                print("No 'Next' button found.")
                return False  # Return False if no buttons are found
        except TimeoutException:
            print("Timeout: 'Next' buttons not found or not clickable.")
            return False  # Return False indicating the action failed due to timeout
        except WebDriverException as e:
            print(f"Web driver error: {e}")
            return False  # Return False indicating the action failed due to a WebDriver issue
        except Exception as e:
            print(f"General error: {e}")
            return False  # Return False indicating the action failed due to some other error
       
    def get_last_message_from_user(self, username):
        try:
            # Fetch all message elements
            messages = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'messageListItem')]")

            # Iterate over messages in reverse to find the last message from the user
            for message in reversed(messages):
                user_elements = message.find_elements(By.XPATH, ".//span[contains(@class, 'username')]")
                if user_elements:
                    user_element = user_elements[-1]
                    if username in user_element.text:
                        # Find the message content
                        return message

            logger.info(f"Message from {username} not found.")
            return None

        except NoSuchElementException:
            logger.info("Error: Unable to locate element.")
            return None
        
    def get_captcha(self):
        try:
            div_element = self.get_last_message_from_user("PokéMeow")
            
            # Find the first a element within the div element
            a_element = div_element.find_elements(By.TAG_NAME, "a")[-1]

            # Now you can get the href attribute or do whatever you need with the a element
            href = a_element.get_attribute("href")
            
            img_path = captcha_service.download_captcha(href)
            
            return captcha_service.send_image(img_path)
        except StaleElementReferenceException:
            logger.error("StaleElementReferenceException occurred. Retrying...")
            time.sleep(1)
            return self.get_captcha()
      
    def get_last_element_by_user(self, username, timeout=30) -> WebElement:
        try:
            # Wait for a new message from the user to appear
            WebDriverWait(self.driver, timeout).until(
                lambda driver: self.check_for_new_message(username)
            )
            
            # Fetch all message elements
            messages = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'messageListItem')]")

            # Iterate over messages in reverse to find the last message from the user
            for message in reversed(messages):
                user_elements = message.find_elements(By.XPATH, ".//span[contains(@class, 'username')]")
                if user_elements:
                    user_element = user_elements[-1]
                    if username in user_element.text:
                        # Return the message element
                        return message

            logger.error(f"Message from {username} not found.")
            return None

        except TimeoutException:
            logger.error(f"Message from {username} not found. Timeout exceeded.")
            return None

        except NoSuchElementException:
            logger.error("Error: Unable to locate element.")
            return None

    def check_for_new_message(self, username):
        # Fetch all message elements
        messages = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'messageListItem')]")

        # Check if the last message is from the user
        if messages:
            try:
                last_message = messages[-1]
                user_elements = last_message.find_elements(By.XPATH, ".//span[contains(@class, 'username')]")
                for user_element in user_elements:
                    if username in user_element.text:
                        return True
                return False
            except StaleElementReferenceException:
                return False

        return False
    
    def wait_for_element_text_to_change(self, element, timeout=15, check_every=1) -> WebElement:
        try:
            # Store the initial text of the element
            initial_text = element.text

            # Wait for the text of the element to change
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # If the text of the element has changed, return the new text
                    if element.text != initial_text:
                        return element
                except StaleElementReferenceException:
                    # If the element is no longer attached to the DOM, return None
                    logger.error("Element is no longer attached to the DOM")
                    return None

                # Wait before checking the text of the element again
                time.sleep(check_every)

            # If the timeout is reached without the text of the element changing, return None
            logger.warning("Timeout reached without text change")
            return None

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None
      
    def solve_captcha(self, element):
        
        #Download the captcha image and send it to the API
        catch_statistics.add_captcha_encounter()
        number = self.get_captcha()
        
        if number is None:
            # If the captcha number is None, try again
            logger.error("Captcha number is None. Trying again...")
            time.sleep(3)
            number = self.get_captcha()
        
        # Write the captcha number in the chat
        logger.info(f"🔢 Captcha response: {number}")
        interruptible_sleep(random.randint(10, 15))
        logger.info("Submitting captcha response...")
        self.write(number)
        
        # Waits 120 seconds for the captcha to be solved
        pokemeow_last_message = self.wait_for_element_text_to_change(element, timeout=120)
        
        if "Thank you" in pokemeow_last_message.text:
            logger.warning('Captcha solved, continuing...')
            return
        else:
            logger.error('Captcha failed, trying again!')
            new_captcha_element = self.get_last_message_from_user("PokéMeow")
            self.solve_captcha(new_captcha_element)
            
    def get_next_ball(self, current_ball):
        
        balls_priority = {
            "masterball": 5,
            "premierball": 4,
            "ultraball": 3,
            "greatball": 2,
            "pokeball": 1
        }

        # Get the priority of the current ball
        current_priority = balls_priority.get(current_ball)

        # If the current ball is not in the dictionary or it's a Pokeball, return None
        if current_priority is None or current_priority == 1:
            return None

        # Find the ball with the next highest priority
        for ball, priority in sorted(balls_priority.items(), key=lambda item: item[1], reverse=True):
            if priority < current_priority:
                return ball
    
    def click_on_ball(self, ball, delay=1):
        # Attempt to find the specific ball first.
        try:
            time.sleep(delay)
            last_element_html = self.get_last_element_by_user("PokéMeow")
            balls = last_element_html.find_elements("css selector",f'img[alt="{ball}"]')
            if balls:
                # If the specific ball is found, click on the last occurrence of that ball.
                balls[-1].click()
            else:
                next_ball = self.get_next_ball(ball)
                logger.warning(f"{ball} not found. Trying {next_ball}")
                if next_ball is None:
                    logger.error("No more balls to try.")
                    return False
                self.click_on_ball(next_ball)
                
        except Exception as e:
            logger.log(f"An error occurred: {e}")
    
    def buy_balls(self, inventory):
        interruptible_sleep(5)
        # Initialize pokecoin count to 0
        budget = 0

        # Iterate over the inventory list
        for item in inventory:
            # Check if the item name is pokecoin
            if item["name"] == "pokecoin":
                # Update pokecoin count
                budget = item["count"]
                if budget > 200000:
                    budget = 200000
                break
            
        commands = Shop.generate_purchase_commands(budget)
        if not commands:
            logger.info("❌Not Enought budget to buy balls.")
            return
        
        for command in commands:
            #Wait 3 scs before writing next command
            logger.info(f'💰 {command}')
            self.write(command)
            interruptible_sleep(5.5)

    def wait_next_message(self, timeout=10):
        # Define the XPath
        xpath = f"//li[contains(@class, 'messageListItem')]"

        # Get the last message that currently matches the XPath
        old_messages = self.driver.find_elements(By.XPATH, xpath)
        old_last_message = old_messages[-1] if old_messages else None

        # Wait for a new message to appear
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: self.driver.find_elements(By.XPATH, xpath)[-1] != old_last_message
            )
            # Get the last message that matches the XPath after waiting
            new_messages = self.driver.find_elements(By.XPATH, xpath)
            # Return the new message
            return new_messages[-1]
        except TimeoutException:
            return None

    def refresh(self):
        logger.info("Refreshing the page...")
        self.driver.refresh()
        # Wait for the element to be visible, not just present
        element_locator = (By.XPATH, "//span[contains(@class, 'emptyText')]")
        WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(element_locator))
        logger.info("Page refreshed successfully.")
        
        
    def print_initial_message(self):
        logger.warning(f"{Fore.GREEN}Autplay Settings:{Style.RESET_ALL}")
        logger.warning("[Autplay settings] AutoBuy enabled: " + str(ENABLE_AUTO_BUY_BALLS))
        logger.warning("[Autplay settings] AutoLootbox enabled: " + str(ENABLE_AUTO_LOOTBOX))
        logger.warning("[Autplay settings] AutoRelease enabled: " + str(ENABLE_RELEASE_DUPLICATES))
        logger.warning("[Autplay settings] AutoQuestReroll enabled: " + str(ENABLE_AUTO_QUEST_REROLL))
        logger.warning("[Autplay settings] AutoEgg enabled: " + str(ENABLE_AUTO_EGG_HATCH))
        logger.warning("[Autplay settings] [FISHING] enabled: " + str(ENABLE_FISHING))
        logger.warning("[Autplay settings] [BATTLE] enabled: " + str(ENABLE_BATTLE_NPC))
        logger.warning("[Autplay settings] [HUNTING] enabled: " + str(ENABLE_HUNTING))
        logger.warning("[Autplay settings] RunPictures enabled: " + str(ENABLE_RUN_PICTURES))
        logger.warning(f"{Fore.GREEN}Autplay Advice:{Style.RESET_ALL}")
        logger.warning("[Autplay Advice] you can pause the bot by pressing 'p' in the console")
        logger.warning("[Autplay Advice] you can see statistics by pressing 's' in the console")
        logger.warning("[Autplay Advice] you can resume the bot by pressing 'enter' in the console")
        logger.warning("[Autplay Advice] you can stop the bot by pressing 'ctrl + c' in the console")
        logger.warning("[Autplay Advice] you ENABLE/DISABLE [BATTLE] by pressing 'b' in the console")
        logger.warning("[Autplay Advice] you ENABLE/DISABLE [FISHING] by pressing 'f' in the console")
        logger.warning("[Autplay Advice] you ENABLE/DISABLE [HUNTING] by pressing 'h' in the console")
        logger.warning(f"[Autplay Advice] you ENABLE/DISABLE [EXPLORE] by pressing 'e' in the console {Fore.RED}(Only for Pokémeow patreons!){Style.RESET_ALL}")
        logger.warning(f"{Fore.GREEN}Config.ini Settings:{Style.RESET_ALL}")
        logger.warning('[config.ini] Default ball for Fishing: %s', fishing_ball)
        logger.warning('[config.ini] Default ball for Pokemons with Held Items: %s', hunt_item_ball)
        logger.warning('[config.ini] Default ball for Shinies or Golden while Fishing: %s', fish_shiny_golden_ball)
        logger.warning("="*60 + "\n")      
        welcome_message = f"""
        {Fore.LIGHTMAGENTA_EX}
            
            ██████╗░░█████╗░██╗░░██╗███████╗███╗░░░███╗███████╗░█████╗░░██╗░░░░░░░██╗ 
            ██╔══██╗██╔══██╗██║░██╔╝██╔════╝████╗░████║██╔════╝██╔══██╗░██║░░██╗░░██║
            ██████╔╝██║░░██║█████═╝░█████╗░░██╔████╔██║█████╗░░██║░░██║░╚██╗████╗██╔╝
            ██╔═══╝░██║░░██║██╔═██╗░██╔══╝░░██║╚██╔╝██║██╔══╝░░██║░░██║░░████╔═████║░
            ██║░░░░░╚█████╔╝██║░╚██╗███████╗██║░╚═╝░██║███████╗╚█████╔╝░░╚██╔╝░╚██╔╝░
            ╚═╝░░░░░░╚════╝░╚═╝░░╚═╝╚══════╝╚═╝░░░░░╚═╝╚══════╝░╚════╝░░░░╚═╝░░░╚═╝░░
            
            ░█████╗░██╗░░░██╗████████╗░█████╗░██████╗░██╗░░░░░░█████╗░██╗░░░██╗
            ██╔══██╗██║░░░██║╚══██╔══╝██╔══██╗██╔══██╗██║░░░░░██╔══██╗╚██╗░██╔╝
            ███████║██║░░░██║░░░██║░░░██║░░██║██████╔╝██║░░░░░███████║░╚████╔╝░
            ██╔══██║██║░░░██║░░░██║░░░██║░░██║██╔═══╝░██║░░░░░██╔══██║░░╚██╔╝░░
            ██║░░██║╚██████╔╝░░░██║░░░╚█████╔╝██║░░░░░███████╗██║░░██║░░░██║░░░
            ╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░░╚════╝░╚═╝░░░░░╚══════╝╚═╝░░╚═╝░░░╚═╝░░░ {Style.RESET_ALL}  Version: {settings.version}

        """
        print(welcome_message)
        print("\n")
    
    def validate(self):
        pokemeow_last_message = self.get_last_message_from_user("PokéMeow")
        
        if pokemeow_last_message is None:
            return
        
        if "A wild Captcha appeared!" in pokemeow_last_message.text:
            logger.warning('Captcha detected!')
            self.solve_captcha(pokemeow_last_message)
