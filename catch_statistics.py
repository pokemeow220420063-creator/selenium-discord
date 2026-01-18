from tabulate import tabulate
from logger import Logger
logger = Logger().get_logger()
import os

class CatchStatistics:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CatchStatistics, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self.rarity_counts = {}
        self.total_coins = 0
        self.items_received = {}
        self.items_received_lootbox = {}
        self.lootboxes_opened = 0
        self.hatch = {}
        self.total_hunt_encounters = 0
        self.total_fish_encounters = 0
        self.total_fish_tokens = 0
        self.total_battles_won = 0
        self.total_captchas_encountered = 0
        self.total_explore_encounters = 0

    def add_catch(self, rarity, coins, item=None):
        # Increment the count for this rarity
        self.rarity_counts[rarity] = self.rarity_counts.get(rarity, 0) + 1

        # Add the coins to the total
        self.total_coins += coins

        # If an item was received, increment its count
        if item is not None:
            self.items_received[item] = self.items_received.get(item, 0) + 1

    def add_lootboxes_opened(self, amount=1):
        self.lootboxes_opened += amount

    def add_hunt_encounter(self):
        self.total_hunt_encounters += 1
    
    def add_coins(self, coins):	
        self.total_coins += coins
        
    def add_item(self, item, amount=1):
        self.items_received[item] = self.items_received.get(item, 0) + amount
    
    def add_item_lootbox(self, item, amount=1):
        self.items_received_lootbox[item] = self.items_received_lootbox.get(item, 0) + amount

    def add_fish_encounter(self, tokens):
        self.total_fish_encounters += 1
        self.total_fish_tokens += tokens

    def add_captcha_encounter(self):
        self.total_captchas_encountered += 1
    
    def add_battles_won(self, coins = 0):
        self.total_battles_won += 1
        self.add_coins(coins)
        
    def add_explore_encounter(self):
        self.total_explore_encounters += 1
        
    def add_hatch(self, pokemon):
        if pokemon is not None:
            self.hatch[pokemon] = self.hatch.get(pokemon, 0) + 1
        
    def get_statistics(self):
        return {
            "RarityCounts": self.rarity_counts,
            "TotalCoins": self.total_coins,
            "ItemsReceived": self.items_received,
            "LootboxesOpened": self.lootboxes_opened,
            "ItemsReceivedLootbox": self.items_received_lootbox,
            "TotalHuntEncounters": self.total_hunt_encounters,
            "TotalFishEncounters": self.total_fish_encounters,
            "TotalExploreEncounters": self.total_explore_encounters,
            "TotalBattlesWon": self.total_battles_won,
            "TotalFishTokens": self.total_fish_tokens,
            "TotalCaptchasEncountered": self.total_captchas_encountered,
            "EggHatches": self.hatch
        }
        

    def print_statistics(self):
        # Get the statistics
        stats = self.get_statistics()

        # Convert the statistics to a list of lists for tabulate
        stats_list = [[key, value] for key, value in stats.items()]
        # Get the size of the console
        columns, _ = os.get_terminal_size()

        table = tabulate(stats_list, headers=['Statistic', 'Value'], tablefmt='pretty')

        padding = (columns - len(table.splitlines()[0])) // 2

        logger.info('\n%s', '\n'.join(' ' * padding + line for line in table.splitlines()))