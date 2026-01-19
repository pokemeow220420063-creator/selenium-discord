# from bs4 import BeautifulSoup
# from commands.handlers.action_handler import ActionHandler
# from driver import Driver
# from helpers.sleep_helper import interruptible_sleep
# from validators.response_validator import evaluate_response
# from logger import Logger
# import time
# from commands.screenshots import ScreenshotHandler
# import os
# from driver import ENABLE_RUN_PICTURES
# from validators.action import Action
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import NoSuchElementException
# from settings import Settings
# import json
# from colorama import Fore, Style
# import re
# from catch_statistics import CatchStatistics
# settings = Settings()
# from helpers.handle_exception import handle_on_start_exceptions

# logger = Logger().get_logger()
# catch_statistics = CatchStatistics()

# # Get the JSON string from the .ini
# pokeball_for_pokemon = settings.pokemon_pokeball_mapping
# rarity_pokeball_mapping = settings.rarity_pokeball_mapping
# rarity_emoji = settings.rarity_emoji
# fishing_ball = settings.fishing_ball
# hunt_item_ball = settings.hunt_item_ball
# fish_shiny_golden_ball = settings.fishing_shiny_golden_ball

# class Fish(ActionHandler):
#     def __init__(self, driver: Driver):
#         super().__init__()
#         self.driver = driver
#         self.logger = Logger().get_logger()
#         self.screenshot_handler = ScreenshotHandler(driver)
#         self.pokemon_info_dict = self.load_pokemon_info()
        
#     @handle_on_start_exceptions
#     def start(self, command:str):
#         self.command = command
#         self.driver.write(command)
#         pokemeow_element_response = self.driver.get_last_element_by_user("PokéMeow", timeout=30)
#         action = evaluate_response(pokemeow_element_response)
        
#         if action is Action.SKIP:
#             interruptible_sleep(2)
#             return
        
#         if action is not Action.PROCEED:
#             self.handle_action(action, self.driver, pokemeow_element_response)
#             return
        
#         li_element = self.driver.wait_for_element_text_to_change(pokemeow_element_response, check_every=0.2)
        
#         if li_element is None:
#             logger.error('No response from PokéMeow while fishing...')
#             return
        
#         try:

#             # Try to pull rod
#             button = li_element.find_element(By.TAG_NAME, "button")
#             time.sleep(0.5)
#             button.click()
            
#             encounter_element = self.driver.wait_for_element_text_to_change(li_element, check_every=1)
            
#             if "The Pokemon got away" in encounter_element.text:
#                 logger.info(f'{Fore.RED}🎣⚠️ The Pokemon got away...{Style.RESET_ALL}')
#                 return
            
#             spawn_info = self.get_spawn_info(encounter_element.get_attribute('outerHTML'))
#             ball = rarity_pokeball_mapping.get(spawn_info["Rarity"], fishing_ball)
#             #IF shiny or golden fish, catch it
#             if spawn_info["Shiny"] or spawn_info["Golden"]:
#                 self.driver.click_on_ball(fish_shiny_golden_ball)
#             else:
#                 if spawn_info["Name"] in pokeball_for_pokemon:
#                     ball = pokeball_for_pokemon[spawn_info["Name"]]
#                     logger.info(f"🔴 Pokemon '{spawn_info['Name']}' found in the dictionary. Using {ball}...")
#                     self.driver.click_on_ball(ball)
#                 else:
#                     self.driver.click_on_ball(fishing_ball)
            
#             catch_status_element = self.driver.wait_for_element_text_to_change(pokemeow_element_response)
            
#             if catch_status_element is None:
#                 logger.error('No response from PokéMeow while fishing...')
#                 return
            
#             self.get_catch_result(spawn_info, 0, catch_status_element)
#             return
#         except NoSuchElementException as e:
            
#             logger.info(f'{Fore.RED}🎣⚠️ Not Even A Nibble...{Style.RESET_ALL}')
#             return


#     def get_spawn_info(self, element):
#         # Parse the HTML content
#         pokemon_info = {}
#         soup = BeautifulSoup(element, "html.parser")
#         # print(soup)
#         pokemon_description = soup.select_one("div[class*='embedDescription']")

#         pokemon_info["Item"] = data = soup.find('img', {'aria-label': ':held_item:'}) is not None

#         if pokemon_description:
#             # Find all strong elements within the description
#             strong_elements = pokemon_description.find_all("strong")


#             if strong_elements:
#                 # Get the last strong element
#                 last_strong_element = strong_elements[-1]

#                 # Extract Pokémon name
#                 pokemon_info["Name"] = last_strong_element.get_text(strip=True)
#                 pokemon_name_lower = pokemon_info["Name"].lower()
#                 pokemon_info["Shiny"] = False
#                 pokemon_info["Golden"] = False
#                 pokemon_info["Legendary"] = False
#                 rarity = self.pokemon_info_dict[pokemon_name_lower]['Rarity']
#                 if pokemon_name_lower in self.pokemon_info_dict:
#                     rarity = self.pokemon_info_dict[pokemon_name_lower]['Rarity']
#                 else:
#                     rarity = None  # replace with a default rarity if 'Horsea' is not in the dictionary
                
                
#                 pokemon_info["Rarity"] = rarity
#                 if "shiny" in pokemon_info["Name"].lower():
#                     pokemon_info["Shiny"] = True
                    
#                 if "golden" in pokemon_info["Name"].lower():
#                     pokemon_info["Golden"] = True

#                 if "legendary" in pokemon_info["Name"].lower():
#                     pokemon_info["Legendary"] = True
#         # print(pokemon_info)
        
#         return pokemon_info
    
#     def load_pokemon_info(self):
#         with open(os.path.join(os.path.dirname(__file__), 'pokemon_info.json'), 'r') as f:
#             pokemon_info_dict = json.load(f)
#             return pokemon_info_dict
    

#     def get_catch_result(self, pokemon_info, count, element):
#         if isinstance(pokemon_info, str):
#             pokemon_info = json.loads(pokemon_info)

#         soup = BeautifulSoup(element.get_attribute('outerHTML'), "html.parser")
#         pokemon_was_catched = soup.find_all(string=lambda text: '✅' in text)
        
#         rarity_color = {
#             'Common': Fore.WHITE,
#             'Uncommon': Fore.WHITE,
#             'Rare': Fore.WHITE,
#             'Super Rare': Fore.CYAN,
#             'Super rare': Fore.CYAN,
#             'Legendary': Fore.MAGENTA,
#             'Shiny': Fore.YELLOW,
#             'Golden': Fore.YELLOW
#         }
        
#         # Load the Pokemon info from the JSON file
#         with open(os.path.join(os.path.dirname(__file__), 'pokemon_info.json'), 'r') as f:
#             pokemon_info_from_file = json.load(f)

#         # Get the Pokemon name and rarity from pokemon_info
#         if 'Name' in pokemon_info:
#             pokemon_name = pokemon_info['Name'].lower()

#         if pokemon_name in self.pokemon_info_dict and 'Rarity' in self.pokemon_info_dict[pokemon_name]:
#             pokemon_rarity = self.pokemon_info_dict[pokemon_name]['Rarity']
#         else:
#             print(f"{pokemon_name} not found in pokemon_info_dict or 'Rarity' not found in pokemon_info_dict[{pokemon_name}]")
#             return
        
#         # Assuming pokemon_rarity is a string like 'Common', 'Uncommon', etc.
#         pokemon_rarity = pokemon_rarity.strip()
#         pokemon_rarity_color = rarity_color[pokemon_rarity]
                
#         has_item = pokemon_info.get('Item')

#         if pokemon_was_catched:
#             footer_text = soup.find('div', class_=lambda value: value and 'embedFooter' in value).get_text(strip=True)
#             fishing_tokens_match = re.search(r'earned (\d+) Fishing Token', footer_text)

#             # Initialize fishing_tokens to 0, then update if found in the text
#             fishing_tokens = 0
#             if fishing_tokens_match:
#                 fishing_tokens = int(fishing_tokens_match.group(1))

#             # Log the catch result with the number of Fishing Tokens earned
#             #Print if shiny or golden fish, if golden print a golden emoji 🟡 if shiny print a shiny emoji
#             catch_statistics.add_fish_encounter(fishing_tokens)
#             if pokemon_info["Shiny"]:
#                 logger.info(f'🎣✨ {Fore.GREEN}Fished a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity}{pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{fishing_tokens} Fishing Tokens{Style.RESET_ALL}')
#                 return {'caught': True, 'fishing_tokens': fishing_tokens}
#             elif pokemon_info["Golden"]:
#                 logger.info(f'🎣🟡 {Fore.GREEN}Fished a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity}{pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{fishing_tokens} Fishing Tokens{Style.RESET_ALL}')
#                 return {'caught': True, 'fishing_tokens': fishing_tokens}
#             elif pokemon_info["Legendary"]:
#                 logger.info(f'🎣🔔 {Fore.GREEN}Fished a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity}{pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{fishing_tokens} Fishing Tokens{Style.RESET_ALL}')
#                 return {'caught': True, 'fishing_tokens': fishing_tokens}

#             # Check if the Pokemon is legendary, shiny, or golden
#             if pokemon_rarity in ['Legendary', 'Shiny', 'Golden'] and ENABLE_RUN_PICTURES:
#                 self.screenshot_handler.take_screenshot_by_element(element, pokemon_name, pokemon_rarity)
            
#             # If the Pokémon was caught, log and return that information
#             logger.info(f'🎣 {Fore.GREEN}Fished a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{fishing_tokens} Fishing Tokens{Style.RESET_ALL}')
#             return {'caught': True, 'fishing_tokens': fishing_tokens}
#         else:
#             # If the Pokémon was not caught, log and return that information
#             logger.info(f'🎣 {Fore.RED}A{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL} {Fore.RED}has failed to fish{Style.RESET_ALL}')
#             catch_statistics.add_fish_encounter(0)
#             return {'caught': False, 'fishing_tokens': 0}