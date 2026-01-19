import re
import asyncio
import os
import numpy as np
from tabulate import tabulate
from logger import Logger
# Import Handler Class
from commands.handlers.action_handler import ActionHandler
from commands.eggs import Egg
from commands.lootbox import Lootbox
from commands.quest import Quest
from commands.grazz import Grazz
from commands.repel import Repel

logger = Logger().get_logger()

# Config environment
ENABLE_AUTO_BUY_BALLS = os.getenv('ENABLE_AUTO_BUY_BALLS') == 'True'
ENABLE_RELEASE_DUPLICATES = os.getenv('ENABLE_RELEASE_DUPLICATES') == 'True'
ENABLE_AUTO_EGG_HATCH = os.getenv('ENABLE_AUTO_EGG_HATCH') == 'True'
ENABLE_AUTO_LOOTBOX = os.getenv('ENABLE_AUTO_LOOTBOX') == 'True' # Fix tên biến ENV
ENABLE_AUTO_QUEST_REROLL = os.getenv('ENABLE_AUTO_QUEST_REROLL') == 'True'
ENABLE_AUTO_GRAZZ_AND_REPEL = os.getenv('ENABLE_AUTO_GRAZZ_AND_REPEL') == 'True'

class Inventory(ActionHandler):
    def __init__(self, driver):
        super().__init__(driver.bot)
        self.driver = driver

    async def actions(self):
        logger.info("[Inventory] Checking Inventory...")
        await self.driver.write(";inv")
        
        message = await self.driver.get_last_element_by_user("PokéMeow", timeout=10)
        if not message:
            logger.info("[Inventory] Failed to get inventory.")
            return

        # Parse trang 1
        full_inventory = self.parse_inventory_message(message)
        
        # Click Next nếu có
        if await self.driver.click_next_button():
            logger.info("[Inventory] Found next page, clicking...")
            message_p2 = await self.driver.wait_for_element_text_to_change(element=message, timeout=10)
            if message_p2:
                items_p2 = self.parse_inventory_message(message_p2)
                full_inventory = self.merge_inventories(full_inventory, items_p2)

        # In log
        # self.print_inventory(full_inventory)

        # Auto Buy Balls
        if ENABLE_AUTO_BUY_BALLS:
            await self.driver.buy_balls(full_inventory)

        # Các module tự động khác
        if ENABLE_AUTO_EGG_HATCH:
            await asyncio.sleep(2)
            await Egg.actions(self.driver, full_inventory)
            
        if ENABLE_AUTO_LOOTBOX:
            await asyncio.sleep(2)
            await Lootbox.actions(self.driver, full_inventory)
            
        if ENABLE_AUTO_QUEST_REROLL:
            await asyncio.sleep(2)
            await Quest.actions(self.driver, full_inventory)

        if ENABLE_AUTO_GRAZZ_AND_REPEL:
            await asyncio.sleep(2)
            await Grazz.actions(self.driver, full_inventory)
            await asyncio.sleep(2)
            await Repel.actions(self.driver, full_inventory)

    @staticmethod
    def parse_inventory_message(message):
        items = []
        if not message or not message.embeds: return items
        for field in message.embeds[0].fields:
            lines = field.value.split('\n')
            for line in lines:
                match = re.search(r'\*\*([\d,]+)\*\*x\s+(.+)', line)
                if match:
                    count = int(match.group(1).replace(',', ''))
                    name = match.group(2).strip().lower()
                    items.append({"name": name, "count": count})
        return items

    @staticmethod
    def merge_inventories(list1, list2):
        merged = {}
        for i in list1 + list2:
            merged[i['name']] = merged.get(i['name'], 0) + i['count']
        return [{"name": k, "count": v} for k, v in merged.items()]

    @staticmethod
    def print_inventory(inventory):
        if not inventory: return
        table = [[i['name'], i['count']] for i in inventory]
        while len(table) % 6 != 0: table.append(['-', '-'])
        try:
            reshaped = np.array(table).reshape(-1, 6)
            logger.info('\n' + tabulate(reshaped, headers=['Item', 'Qty']*3))
        except:
            logger.info(f"Inventory: {len(inventory)} items.")