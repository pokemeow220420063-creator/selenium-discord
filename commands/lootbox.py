from bs4 import BeautifulSoup
from driver import Driver
from helpers.sleep_helper import interruptible_sleep
from logger import Logger
from settings import Settings
from catch_statistics import CatchStatistics
settings = Settings()
catch_statistics = CatchStatistics()
logger = Logger().get_logger()

class Lootbox:
    @staticmethod
    def actions(driver: Driver, inventory):
        logger.info(f"[Lootbox] You have {Lootbox.get_lootbox_amount(inventory)} lootbox...")
        if Lootbox.get_lootbox_amount(inventory) >= 10:
            logger.info(f"Opening {Lootbox.get_lootbox_amount(inventory)} lootbox...")
            driver.write(";lb all")
            lootbox_response = driver.get_last_element_by_user("PokéMeow", timeout=30)
            if lootbox_response is None:
                logger.warning("[Lootbox] Failed to open lootbox or to get response...")
                return
            items = Lootbox.extract_items(lootbox_response.get_attribute('innerHTML'))
            logger.info(f"[Lootbox] Items Earned:")
            catch_statistics.add_lootboxes_opened(Lootbox.get_lootbox_amount(inventory))
            for item in items:
                catch_statistics.add_item_lootbox(item, items[item])
                logger.info(f"[Lootbox] {item}: {items[item]}")
                
        
    @staticmethod
    def get_lootbox_amount(inventory) -> int:
        return next((item['count'] for item in inventory if item['name'] == 'lootbox'), None)
    
    @staticmethod
    def extract_items(html):
        soup = BeautifulSoup(html, 'html.parser')
        items = {}
        
        # Find all strong tags where quantities are located
        quantity_tags = soup.find_all('strong')
        
        for tag in quantity_tags:
            # Checking if the text contains 'x' which indicates a quantity
            if 'x' in tag.text:
                try:
                    # Following sibling for each tag, which should be the img tag
                    item_img = tag.find_next('img')
                    if item_img:
                        # Extracting the number of items
                        quantity = int(tag.text.strip().replace(' x', '').replace(',', ''))
                        # Extracting the item name from the alt attribute of the img tag
                        item_name = item_img['alt'].strip(':')
                        items[item_name] = quantity
                except ValueError:
                    # In case the conversion fails
                    continue

        return items
