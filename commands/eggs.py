from bs4 import BeautifulSoup
import json
from selenium.webdriver.remote.webelement import WebElement
from helpers.sleep_helper import interruptible_sleep
from driver import Driver
from logger import Logger
import colorama
from colorama import Fore, Back, Style
from catch_statistics import CatchStatistics

catch_statistics = CatchStatistics()
logger = Logger().get_logger()
class Egg:
    
    @staticmethod
    def get_egg_status(html_content):
        # Check if html_content is a WebElement
        if isinstance(html_content, WebElement):
            html_content = html_content.get_attribute('outerHTML')

        soup = BeautifulSoup(html_content, 'html.parser')
        # Check for READY TO HATCH
        ready_to_hatch = soup.find(string="[READY TO HATCH!]")
        if ready_to_hatch:
            return {"can_hatch": True, "can_hold": False}

        # Check for holding egg with counter
        counter = soup.find(string=lambda text: "[COUNTER:" in text)
        if counter:
            return {"can_hatch": False, "can_hold": False}

        # Check for no egg and no holding
        eggs = soup.find_all(string=lambda text: "x Eggs" in text)
        for egg in eggs:
            if "0x Eggs" in egg:
                return {"can_hatch": False, "can_hold": True}

        # If none of the conditions above are met, we cannot determine the status
        return {"can_hatch": False, "can_hold": True}
    
    @staticmethod
    def get_hatch_result(html_content):
        # Check if html_content is a WebElement
        if isinstance(html_content, WebElement):
            html_content = html_content.get_attribute('outerHTML')
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the text 'just hatched a' to locate the general area where the Pokémon name is expected
        hatched_text = soup.find(text=lambda t: "just hatched a" in t)
        
        # Find the next strong tag after the 'just hatched a' text, which should contain the Pokémon name
        if hatched_text and hatched_text.find_next("strong"):
            pokemon_name = hatched_text.find_next("strong").text
        else:
            pokemon_name = None

        return pokemon_name  # Make sure to return the result
    
    @staticmethod
    def actions(driver:Driver, inventory):
        logger.info("[Egg] Checking Eggs...")
        can_hold_egg = False
        # if ENABLE_AUTO_EGG_HATCH:
        egg_status = Egg.get_egg_status(driver.get_last_message_from_user("PokéMeow"))
        # logger.info(f"[Egg actions] Egg status: {egg_status}")
        if egg_status["can_hatch"]:
                interruptible_sleep(3)
                logger.info(f"{Fore.YELLOW}🐣 Hatching egg...{Style.RESET_ALL}")
                driver.write(";egg hatch")
                can_hold_egg = True
                hatch_element = driver.get_last_element_by_user("PokéMeow", timeout=30)
                interruptible_sleep(6)
                if hatch_element is not None:
                    pokemon_hatched = Egg.get_hatch_result(hatch_element)
                    catch_statistics.add_hatch(pokemon_hatched)
                    logger.info(f"🐣{Fore.GREEN} A {Style.RESET_ALL}{Fore.LIGHTCYAN_EX}{pokemon_hatched}{Style.RESET_ALL} {Fore.GREEN}has been hatched!{Style.RESET_ALL}")
                    
                    
                    
        # Check if can hold egg
        poke_egg_count = next((item['count'] for item in inventory if item['name'] == 'poke_egg'), None)
        if poke_egg_count > 0:
            if egg_status["can_hold"] or can_hold_egg:
                logger.info(f"{Fore.YELLOW}🥚 Holding egg...{Style.RESET_ALL}")
                driver.write(";egg hold")
                interruptible_sleep(2.5)