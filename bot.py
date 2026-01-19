import random
import os
from helpers.scheduler import Scheduler, Task
# from commands.battle import Battle
# from commands.fish import Fish
from commands.pokemon import Pokemon
from commands.inventory import Inventory
from commands.catchbot import CatchBot
from commands.daily import Daily
from commands.release import Release

# Load settings ENV để bật tắt task
ENABLE_FISHING = os.getenv('ENABLE_FISHING', 'True') == 'True'
ENABLE_BATTLE_NPC = os.getenv('ENABLE_BATTLE_NPC', 'True') == 'True'
ENABLE_HUNTING = os.getenv('ENABLE_HUNTING', 'True') == 'True'
ENABLE_EXPLORING = os.getenv('ENABLE_EXPLORING', 'True') == 'True'
ENABLE_CATCHBOT = os.getenv('ENABLE_CATCHBOT', 'True') == 'True'
ENABLE_DAILY = os.getenv('ENABLE_DAILY', 'True') == 'True'
ENABLE_RELEASE_DUPLICATES = os.getenv('ENABLE_RELEASE_DUPLICATES', 'True') == 'True'

class Bot:
    
    def __init__(self, driver):
        self.driver = driver # Driver Async
        self.scheduler = Scheduler()
        
        # Khởi tạo Modules (Truyền driver vào)
        # self.battle = Battle(driver)
        # self.fish = Fish(driver)
        self.pokemon = Pokemon(driver)
        self.inventory = Inventory(driver) # Inventory cần sửa init để nhận driver
        self.catchbot = CatchBot(driver)
        self.daily = Daily(driver)
        self.release = Release(driver)
        
        # Mapping cấu hình
        task_settings = {
            'inventory_task': [True],
            # 'fishing_task': [ENABLE_FISHING],
            'hunting_task': [ENABLE_HUNTING],
            # 'battle_task': [ENABLE_BATTLE_NPC],
            'catchbot_task': [ENABLE_CATCHBOT],
            'daily_task': [ENABLE_DAILY],
            'release_task': [ENABLE_RELEASE_DUPLICATES],
        }
        
        # Tạo Task (Lambda gọi hàm ASYNC)
        # Lưu ý: Các hàm như self.pokemon.start phải là 'async def'
        self.inventory_task = Task(lambda: self.inventory.actions(), lambda: (7*4)*50)
        # self.battle_task = Task(lambda: self.battle.start(";b npc 1"), lambda: random.randint(39, 42))
        # self.fishing_task = Task(lambda: self.fish.start(";f"), lambda: random.randint(19, 21))
        self.hunting_task = Task(lambda: self.pokemon.start(";p"), lambda: random.randint(7, 11))
        self.catchbot_task = Task(lambda: self.catchbot.start(";cb run"), lambda: random.randint(3600, 3700))
        self.daily_task = Task(lambda: self.daily.start(";daily"), lambda: random.randint(86400, 86400))
        self.release_task = Task(lambda: self.release.actions(), lambda: random.randint(1800, 3600))
        
        # Add tasks
        self.scheduler.add_task(self.inventory_task)
        # self.scheduler.add_task(self.battle_task)
        # self.scheduler.add_task(self.fishing_task)
        self.scheduler.add_task(self.hunting_task)
        self.scheduler.add_task(self.catchbot_task)
        self.scheduler.add_task(self.daily_task)
        self.scheduler.add_task(self.release_task)
        
        # Enable/Disable tasks based on settings
        for task_name, settings_list in task_settings.items():
            if hasattr(self, task_name):
                task = getattr(self, task_name)
                if any(settings_list):
                    task.enable()
                else:
                    task.disable()

    async def run(self):
        # Chạy Scheduler Async
        await self.scheduler.run()

    def enable_task(self, task): task.enable()
    def disable_task(self, task): task.disable()
    
    def switch_task(self, task):
        if task.enabled: self.disable_task(task)
        else: self.enable_task(task)