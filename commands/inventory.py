from bs4 import BeautifulSoup
import json
from selenium.webdriver.remote.webelement import WebElement
from helpers.sleep_helper import interruptible_sleep
from logger import Logger
from commands.eggs import Egg
from commands.lootbox import Lootbox
from commands.quest import Quest
from commands.grazz import Grazz
from commands.repel import Repel
import os
logger = Logger().get_logger()

ENABLE_AUTO_BUY_BALLS = os.getenv('ENABLE_AUTO_BUY_BALLS') == 'True'
ENABLE_RELEASE_DUPLICATES = os.getenv('ENABLE_RELEASE_DUPLICATES') == 'True'
ENABLE_AUTO_EGG_HATCH = os.getenv('ENABLE_AUTO_EGG_HATCH') == 'True'
ENABLE_AUTO_LOOTBOX = os.getenv('ENABLE_AUTO_LOOTBOX_OPEN') == 'True'
ENABLE_AUTO_QUEST_REROLL = os.getenv('ENABLE_AUTO_QUEST_REROLL') == 'True'
ENABLE_AUTO_GRAZZ_AND_REPEL = os.getenv('ENABLE_AUTO_GRAZZ_AND_REPEL') == 'True'

class Inventory:
    
    @staticmethod
    def check_inventory(driver):
        logger.info("[Inventory] Checking Inventory...")
        interruptible_sleep(1)
        driver.write(";inv")

        last_element_html = driver.get_last_element_by_user("PokéMeow")
        inventory_json = Inventory.get_inventory_json(last_element_html)
        
        if not inventory_json:
            logger.info("[Inventory] Failed to get inventory.")
            return
        
        if inventory_json is None:
            logger.info("[Inventory] Failed to get inventory, inventory None.")
            return
        
        if ENABLE_AUTO_EGG_HATCH:
            interruptible_sleep(2)
            Egg.actions(driver, json.loads(inventory_json))
            
        if ENABLE_AUTO_LOOTBOX:
            interruptible_sleep(3)
            Lootbox.actions(driver, json.loads(inventory_json))
        if ENABLE_AUTO_QUEST_REROLL:
            interruptible_sleep(3)
            Quest.actions(driver, inventory)

        if ENABLE_AUTO_GRAZZ_AND_REPEL:
            interruptible_sleep(3)
            Grazz.actions(driver, json.loads(inventory_json))
            interruptible_sleep(3)
            Repel.actions(driver, json.loads(inventory_json))
            
        if not driver.click_next_button():
            inventory = json.loads(inventory_json)
            Inventory.print_inventory(inventory)
            return inventory
        
        logger.info("[Inventory] Checking second page of inventory...")
        last_element_html = driver.wait_for_element_text_to_change(last_element_html)
        if last_element_html is None:
            logger.info("[Inventory] Failed to get Second page of Inventory.")
            inventory = json.loads(inventory_json)
            
            return inventory
        #include the next page of inventory
        inventory_json_second_page = Inventory.get_inventory_json(last_element_html)
        
        if not inventory_json_second_page or inventory_json_second_page is None:
            logger.info("[Inventory] Failed to get inventory.")
            inventory = json.loads(inventory_json)
            return inventory
        
        # Load JSON into a Python object
        inventory_json = Inventory.merge_inventories(inventory_json, inventory_json_second_page)
        inventory = json.loads(inventory_json)
        # Inventory.print_inventory(inventory)
            
        return inventory
    
    @staticmethod
    def get_inventory_json(html_content):
        import re
         # Function to check if a tag contains a partial class name
        def contains_partial_class(partial):
            return re.compile(".*" + partial + ".*")
        try:
            # Check if html_content is a WebElement
            if isinstance(html_content, WebElement):
                html_content = html_content.get_attribute('outerHTML')

            # print(html_content)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Initialize a list to store each item in a flat structure
            items_list = []
            
            # Find all categories
            # categories = soup.find_all("div", class_="embedFieldName_d42d0c")
            categories = soup.find_all("div", class_=contains_partial_class("embedFieldName"))
            
            for category in categories:
                category_name = category.get_text(strip=True)
                # item_container = category.find_next_sibling("div", class_="embedFieldValue_f2dcec")
                item_container = category.find_next_sibling("div", class_=contains_partial_class("embedFieldValue"))

                if item_container:
                    for item in item_container.find_all("span", class_=contains_partial_class("emojiContainer")):
                        item_name = item.img['alt'] if item.img else "Unknown"
                        count_text = item.find_next_sibling("strong")
                        count = count_text.get_text(strip=True) if count_text else "0"
                        
                        # Try to convert count to an integer
                        try:
                            count = int(count.replace(",", ""))
                        except ValueError:
                            # If count is not an integer, set it to -1
                            count = -1
                        
                        item_dict = {
                            "name": item_name. replace(":", "").lower(),
                            "count": count
                        }
                        items_list.append(item_dict)
            
            # Convert the list of items to JSON
            items_json = json.dumps(items_list, indent=4)
            return items_json
        except Exception as e:
            logger.error(f"[Inventory] An error occurred while getting the inventory JSON: {e}")
            return None
    
    @staticmethod
    def print_inventory(inventory):
        from tabulate import tabulate
        import numpy as np

        # Convert list of dictionaries to list of lists
        table = [[item['name'], item['count']] for item in inventory]

        # Pad the table with dummy data until its size is a multiple of 6
        while len(table) % 6 != 0:
            table.append(['-', '-'])

        # Reshape the table into a multi-column format
        num_columns = 6
        reshaped_table = np.array(table).reshape(-1, num_columns)

        # Print table
        logger.info('\n' + tabulate(reshaped_table, headers=['Item Name', 'Count']*3))
    
    @staticmethod
    def merge_inventories(inventory_json, inventory_json_second_page):
        # Convert JSON to list of dictionaries
        inventory1 = json.loads(inventory_json)
        inventory2 = json.loads(inventory_json_second_page)

        # Merge inventories
        for item2 in inventory2:
            # Check if item already exists in inventory1
            for item1 in inventory1:
                if item1['name'] == item2['name']:
                    # If item exists, add the counts
                    item1['count'] += item2['count']
                    break
            else:
                # If item does not exist, add it to the inventory
                inventory1.append(item2)

        # Convert back to JSON
        merged_inventory_json = json.dumps(inventory1, indent=4)
        return merged_inventory_json