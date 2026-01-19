# from bs4 import BeautifulSoup
# from commands.handlers.action_handler import ActionHandler
# from driver import Driver
# from helpers.sleep_helper import interruptible_sleep
# from validators.response_validator import evaluate_response
# from logger import Logger
# from driver import ENABLE_RUN_PICTURES
# import os
# from commands.screenshots import ScreenshotHandler
# from validators.action import Action
# from settings import Settings
# import json
# import re
# from colorama import Fore, Style
# from catch_statistics import CatchStatistics
# from commands.inventory import Inventory
# from helpers.handle_exception import handle_on_start_exceptions
# from selenium.webdriver.common.by import By
# import random
# import random
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# settings = Settings()

# logger = Logger().get_logger()
# catch_statistics = CatchStatistics()

# # Get the JSON string from the .ini
# pokeball_for_pokemon = settings.pokemon_pokeball_mapping
# rarity_pokeball_mapping = settings.rarity_pokeball_mapping
# rarity_emoji = settings.rarity_emoji
# fishing_ball = settings.fishing_ball
# hunt_item_ball = settings.hunt_item_ball
# fish_shiny_golden_ball = settings.fishing_shiny_golden_ball

# arrow_images = [
#     'up_left', 'up_arrow', 'up_right',
#     'left_arrow', 'right_arrow',
#     'down_left', 'down_arrow', 'down_right'
# ]

# rarity_color = {
#             'Common': Fore.WHITE,
#             'Uncommon': Fore.WHITE,
#             'Rare': Fore.WHITE,
#             'Super Rare': Fore.CYAN,
#             'Super rare': Fore.CYAN,
#             'Legendary': Fore.MAGENTA,
#             'Shiny': Fore.MAGENTA,
#             'Golden': Fore.MAGENTA
#         }

# class Explore(ActionHandler):
#     def __init__(self, driver: Driver):
#         super().__init__()
#         self.driver = driver
#         self.logger = Logger().get_logger()
#         self.encounter_counter = 0
#         self.pokemon_info_dict = self.load_pokemon_info()

#     @handle_on_start_exceptions
#     def start(self, commands):
#         self.command = random.choice(commands)
#         self.driver.write(self.command)
#         pokemeow_element_response = self.driver.get_last_element_by_user("PokéMeow", timeout=15)
#         action = evaluate_response(pokemeow_element_response)
#         if action is Action.SKIP:
#             interruptible_sleep(2)
#             return
        
#         if action is not Action.PROCEED:
#             self.handle_action(action, self.driver, pokemeow_element_response)
#             return
        
#         if "Welcome to" not in pokemeow_element_response.text:
#             self.logger.error("🗺️ Something happened...")
#             self.logger.error(pokemeow_element_response.text)
#             return
#         steps = 0
#         while True:
#             interruptible_sleep(0.1)
#             enabled_buttons = self.get_enabled_buttons(pokemeow_element_response)
#             if not enabled_buttons:
#                 continue
            
#             arrow = random.choice(enabled_buttons)
#             arrow.click()
#             steps += 1
#             element_updated = self.driver.wait_for_element_text_to_change(pokemeow_element_response, timeout=3, check_every=0.2)
#             if element_updated is None:
#                 self.logger.info(f"🗺️ Explore session has ended with {steps} steps.")
#                 element = self.driver.get_last_message_from_user("PokéMeow")
#                 self.click_on_run(element)
#                 break
#             if "explore session has ended" in element_updated.text:
#                 self.logger.info(f"🗺️ Explore session has ended with {steps} steps.")
#                 element = self.driver.get_last_message_from_user("PokéMeow")
#                 self.click_on_run(element)
#                 break
#             encounter_info = self.get_pokemon_name(element_updated.get_attribute('outerHTML'))
#             if encounter_info is None:
#                 self.logger.info(f"🗺️ {Fore.LIGHTBLUE_EX}[{steps}] {Fore.GREEN}No Pokémon found...{Style.RESET_ALL}")
#                 continue
            
#             pokemon_name = encounter_info
#             try:
#                 encounter_info = self.pokemon_info_dict[encounter_info.lower()]
#             except KeyError:
#                 self.logger.error(f"🗺️ {Fore.LIGHTBLUE_EX}[{steps}] {Fore.RED}Error: Pokémon '{pokemon_name}' not found in the dictionary...{Style.RESET_ALL}")
#                 # Save an screenshot
#                 ScreenshotHandler(self.driver.driver).take_screenshot_by_element(element_updated, "WEB_ELEMENT_TEST")
#                 # save the element into an index.html file
#                 with open('index.html', 'w') as f:
#                     f.write(element_updated.get_attribute('outerHTML'))
#                 continue
#             rarity = encounter_info["Rarity"]
#             ball = rarity_pokeball_mapping.get(rarity)
#             color = rarity_color.get(rarity, Fore.RESET) 
            
#             if pokemon_name in pokeball_for_pokemon:
#                 ball = pokeball_for_pokemon[pokemon_name]
#                 self.logger.info(f"🔴 Pokemon '{pokemon_name}' found in the dictionary. Using {ball}...")
#                 self.driver.click_on_ball(ball, delay=0.2)
#             else:
#                 self.driver.click_on_ball(ball, delay=0.2)
            
#             encounter_element_result = self.driver.wait_for_element_text_to_change(element_updated, timeout=3, check_every=0.2)
#             if encounter_element_result is None:
#                 continue
#             coins_earned = self.get_encounter_result(encounter_element_result.get_attribute('outerHTML'))
#             if coins_earned is not None:
#                 catch_statistics.add_catch(rarity, coins=int(coins_earned.replace(',', '')))
#                 logger.info(f"🗺️ {Fore.LIGHTBLUE_EX}[{steps}] {Style.RESET_ALL}{Fore.GREEN}Caught a {Style.RESET_ALL}{color}{rarity} {pokemon_name}!{Style.RESET_ALL} {Fore.YELLOW}Earned {coins_earned} coins{Style.RESET_ALL}")
#             else:
#                 logger.info(f"🗺️ {Fore.LIGHTBLUE_EX}[{steps}] {Style.RESET_ALL}{Fore.RED}Failed to catch a{Style.RESET_ALL} {color}{rarity} {pokemon_name}{Style.RESET_ALL}")
#             catch_statistics.add_explore_encounter()
                
#     def get_encounter_result(self, html_content):
#         soup = BeautifulSoup(html_content, 'html.parser')
        
#         if "Congratulations" not in soup.get_text():
            
#             return None
        
#         pokecoin_img = soup.find('img', {'aria-label': ':PokeCoin:'})

#         if pokecoin_img:
#             parent_element = pokecoin_img.find_parent('li')
            
#             if parent_element:
#                 text_after = parent_element.get_text(separator=' ').split('You earned')[-1].strip()
                
#                 coins_earned = ''.join(c for c in text_after if c.isdigit() or c == ',')
#                 return coins_earned

#         return '0'

#     def get_pokemon_name(self, element):
#         """
#         Extracts the Pokémon name from an HTML element.

#         :param element: String containing the HTML content to parse
#         :return: The Pokémon name or None if no Pokémon appears
#         """
#         # Parse the HTML content using BeautifulSoup
#         soup = BeautifulSoup(element, 'html.parser')
        
#         # Check if "No Pokemon appeared" is present in the text
#         if "No Pokemon appeared" in soup.get_text():
#             return None
        
#         # Find all <strong> tags in the document
#         strong_tags = soup.find_all('strong')
#         return strong_tags[-1].get_text()

#     def get_enabled_buttons(self, element):
#         enabled_buttons = []
#         for img_alt in arrow_images:
#             try:
#                 # Find the button wrapping the image with the specified alt attribute
#                 button = element.find_element(By.XPATH, f'.//button[not(@disabled)]//img[@alt="{img_alt}"]')
#                 enabled_buttons.append(button)
#             except Exception as e:
#                 pass
#         return enabled_buttons
        
#     def load_pokemon_info(self):
#         with open(os.path.join(os.path.dirname(__file__), 'pokemon_info.json'), 'r') as f:
#             pokemon_info_dict = json.load(f)
#             return pokemon_info_dict
        
#     def click_on_run(self, element):
#         # Iterate over each button to find the one with the specific alt text
#         buttons = element.find_elements(By.XPATH, ".//button")
#         for button in buttons:
#             try:
#                 # Find the img element inside the button
#                 img = button.find_element(By.TAG_NAME, 'img')
#                 # Check if the img's alt attribute matches 'run'
#                 if img.get_attribute('alt') == 'run':
#                     # Click the button containing the image with alt='run'
#                     button.click()
#                     break
#             except Exception as e:
#                 # Handle potential errors if the img tag isn't found within the button
#                 self.logger.error(f"Error processing button: {e}")
    
#     def pause(self):
#         catch_statistics.print_statistics()
#         from instances.bot_instance import bot
        
#         bot.disable_task(bot.explore_task)
#         logger.warning('[Explore] Action Explore is disabled.')