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

class Daily(ActionHandler):
    def __init__(self, driver: Driver):
        super().__init__()
        self.driver = driver
        self.logger = Logger().get_logger()

    @handle_on_start_exceptions
    def start(self, command: str = ";daily"):
        self.logger.info(f"[Daily] Checking Daily Reward...")
        self.driver.write(command)
        
        element_response = self.driver.get_last_element_by_user("PokéMeow", timeout=15)

        # Retry logic
        if "Please wait" in element_response.text:
            self.logger.info(f"[Daily] Please wait. Retrying...")
            interruptible_sleep(4)
            return self.start(command)

        # Validate Captcha/Ban
        action = evaluate_response(element_response)
        if action is Action.SKIP:
            interruptible_sleep(2)
            return
        if action is not Action.PROCEED:
            self.handle_action(action, self.driver, element_response)
            return

        self.process_daily_response(element_response)

    def process_daily_response(self, element):
        soup = BeautifulSoup(element.get_attribute('outerHTML'), "html.parser")
        
        # Remove reply context
        for reply in soup.find_all(class_=re.compile("repliedMessage")):
            reply.decompose()

        full_text = soup.get_text(separator=' ', strip=True)
        full_text_lower = full_text.lower()

        # Case 1: Success
        if "daily streak" in full_text_lower and "pokecoins" in full_text_lower:
            coins_match = re.search(r'([\d,]+)\s+PokeCoins', full_text, re.IGNORECASE)
            streak_match = re.search(r'(\d+)\s+daily streak', full_text, re.IGNORECASE)
            
            coins = coins_match.group(1) if coins_match else "?"
            streak = streak_match.group(1) if streak_match else "?"

            self.logger.info(
                f"{Fore.GREEN}[Daily]{Style.RESET_ALL} {Fore.GREEN}Claimed!{Style.RESET_ALL} "
                f"Coins: {Fore.YELLOW}{coins}{Style.RESET_ALL} | {Fore.GREEN}Streak:{Style.RESET_ALL} {Fore.CYAN}{streak}{Style.RESET_ALL}"
            )
            return

        # Case 2: Cooldown
        elif "must wait" in full_text_lower:
            strong_tag = soup.find("strong")
            if strong_tag:
                time_wait = strong_tag.get_text(strip=True)
            else:
                match = re.search(r'wait.*?(?:[:\w]+:)?\s*(\d+H\s*\d+M\s*\d+S|\d+H|\d+M|\d+S).*?until', full_text, re.IGNORECASE)
                time_wait = match.group(1) if match else "Unknown"

            self.logger.info(
                f"{Fore.GREEN}[Daily]{Style.RESET_ALL} "
                f"{Fore.GREEN}Not Ready.{Style.RESET_ALL} "
                f"{Fore.GREEN}Wait:{Style.RESET_ALL} {Fore.CYAN}{time_wait}{Style.RESET_ALL}"
            )
            return

        # Case 3: Already claimed (Rare)
        elif "already claimed" in full_text_lower:
             self.logger.info(f"[Daily] Already claimed today.")
             return

        # Case 4: Unknown
        else:
            self.logger.warning(f"[Daily] Unknown response: {full_text[:60]}...")