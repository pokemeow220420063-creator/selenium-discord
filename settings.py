# settings.py
import configparser
import json
from tabulate import tabulate

config = configparser.ConfigParser()

class Settings:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        # Create a ConfigParser object
        self.config = configparser.ConfigParser()

        # Read the config.ini file
        with open('config.ini', 'r', encoding='utf-8') as f:
            self.config.read_file(f)

        # Access the settings
        settings = self.config['settings']

        # Parse the JSON data
        self.version = json.loads(settings['version'])
        self.rarity_emoji = json.loads(settings['rarity_emoji'])
        self.rarity_pokeball_mapping = json.loads(settings['rarity_pokeball_mapping'])
        self.pokemon_pokeball_mapping = json.loads(settings['pokemon_pokeball_mapping'])

        # Access the other settings
        self.fishing_ball = settings['fishing_ball']
        self.hunt_item_ball = settings['hunt_item_ball']
        self.fishing_shiny_golden_ball = settings['fishing_shiny_golden_ball']
        self.driver_path = settings['driver_path']
        self.predict_captcha_url = settings['predict_captcha_url']
        self.send_id = settings['send_id']
        self.webhook_url = settings['webhook_url']
        
        # self.log_settings()
        
    def log_settings(self):
        from logger import Logger  # Delayed import here
        logger = Logger().get_logger()

        # Iterate over all attributes of the settings
        for attr in vars(self):
            value = getattr(self, attr)
            # Check if the value is a dictionary
            if isinstance(value, dict):
                # Convert the dictionary to a list of lists and print it as a table
                table = [[key, val] for key, val in value.items()]
                logger.info(f"\n{attr}:\n{'-' * len(attr)}")
                for row in table:
                    logger.info(f"{row[0]}: {row[1]}")
            else:
                # print the value
                logger.info(f"\n{attr}: {value}\n{'-' * len(attr)}")
