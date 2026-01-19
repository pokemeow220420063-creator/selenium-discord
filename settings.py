import configparser
import json
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self.config = configparser.ConfigParser()
        
        # Đọc config.ini (nếu có)
        if os.path.exists('config.ini'):
            with open('config.ini', 'r', encoding='utf-8') as f:
                self.config.read_file(f)

        settings = self.config['settings'] if 'settings' in self.config else {}

        # Parse JSON data
        self.version = json.loads(settings.get('version', '"1.0"'))
        self.rarity_emoji = json.loads(settings.get('rarity_emoji', '{}'))
        self.rarity_pokeball_mapping = json.loads(settings.get('rarity_pokeball_mapping', '{}'))
        self.pokemon_pokeball_mapping = json.loads(settings.get('pokemon_pokeball_mapping', '{}'))

        # Simple settings
        self.fishing_ball = settings.get('fishing_ball', 'pokeball')
        self.hunt_item_ball = settings.get('hunt_item_ball', 'pokeball')
        self.fishing_shiny_golden_ball = settings.get('fishing_shiny_golden_ball', 'masterball')
        self.webhook_url = settings.get('webhook_url', '')

        # Load Env
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.channel_id = int(os.getenv('CHANNEL_ID', '0')) # Bắt buộc phải có để Driver biết chat ở đâu