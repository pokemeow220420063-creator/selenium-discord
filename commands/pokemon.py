from bs4 import BeautifulSoup
from commands.handlers.action_handler import ActionHandler
from driver import Driver
from helpers.sleep_helper import interruptible_sleep
from validators.response_validator import evaluate_response
from logger import Logger
from driver import ENABLE_RUN_PICTURES
import os
from commands.screenshots import ScreenshotHandler
from validators.action import Action
from settings import Settings
import json
import re
from colorama import Fore, Style
from catch_statistics import CatchStatistics
from commands.inventory import Inventory
from helpers.handle_exception import handle_on_start_exceptions
settings = Settings()

logger = Logger().get_logger()
catch_statistics = CatchStatistics()

# Get the JSON string from the .ini
pokeball_for_pokemon = settings.pokemon_pokeball_mapping
rarity_pokeball_mapping = settings.rarity_pokeball_mapping
rarity_emoji = settings.rarity_emoji
fishing_ball = settings.fishing_ball
hunt_item_ball = settings.hunt_item_ball
fish_shiny_golden_ball = settings.fishing_shiny_golden_ball

class Pokemon(ActionHandler):
    def __init__(self, driver: Driver):
        super().__init__()
        self.driver = driver
        self.logger = Logger().get_logger()
        self.encounter_counter = 0
        self.screenshot_handler = ScreenshotHandler(driver)
        self.pokemon_info_dict = self.load_pokemon_info()

    @handle_on_start_exceptions
    def start(self, command:str):
        self.command = command
        self.driver.write(command)
        pokemeow_element_response = self.driver.get_last_element_by_user("PokéMeow", timeout=15)
        action = evaluate_response(pokemeow_element_response)
        
        if action is Action.SKIP:
            interruptible_sleep(2)
            return
        
        if action is not Action.PROCEED:
            self.handle_action(action, self.driver, pokemeow_element_response)
            return
        
        spawn_json = self.get_spawn_info(pokemeow_element_response)
        spawn_info = json.loads(spawn_json)
        
        rarity = spawn_info["Rarity"]
        ball = rarity_pokeball_mapping.get(rarity)
        has_item = spawn_info["Item"]
        if has_item and rarity not in "Legendary" and rarity not in "Shiny":
            self.driver.click_on_ball(hunt_item_ball)
        else:
            if spawn_info["Name"] in pokeball_for_pokemon:
                ball = pokeball_for_pokemon[spawn_info["Name"]]
                logger.info(f"🔴 Pokemon '{spawn_info['Name']}' found in the dictionary. Using {ball}...")
                self.driver.click_on_ball(ball)
            else:
                self.driver.click_on_ball(ball)
                
        self.encounter_counter += 1
        catch_status_element = self.driver.wait_for_element_text_to_change(pokemeow_element_response)
        self.get_catch_result(spawn_json, self.encounter_counter, catch_status_element)

        if spawn_info["Balls"]["Pokeballs"] <= 1 or spawn_info["Balls"]["Greatballs"] <= 1:
                    inventory = Inventory.check_inventory(self.driver)
                    self.driver.buy_balls(inventory)
    
    
    def get_spawn_info(self, element):
        
        pokemon_info = {}
        
        # Parse the HTML content
        soup = BeautifulSoup(element.get_attribute('outerHTML'), "html.parser")
        # Find the element containing the Pokémon description
        pokemon_description = soup.select_one("div[class*='embedDescription']")

        pokemon_info["Item"] = data = soup.find('img', {'aria-label': ':held_item:'}) is not None

        if pokemon_description:
            # Find all strong elements within the description
            strong_elements = pokemon_description.find_all("strong")

            if strong_elements:
                # Get the last strong element
                last_strong_element = strong_elements[-1]

                # Extract Pokémon name
                pokemon_info["Name"] = last_strong_element.get_text(strip=True)
                
        # span = soup.find('span', {'class': 'embedFooterText_dc937f'}) 
        span = soup.select_one("span[class*='embedFooterText']")

        text = span.get_text()
        # Use a regular expression to find the rarity
        rarity = re.search(r'(.+?)\s*\(', span.get_text())

        # Check if a match was found
        if rarity:
            # Get the first group of the match
            rarity = rarity.group(1).strip()
            pokemon_info["Rarity"] = rarity

        # Use a regular expression to find all occurrences of 'word: number'
        matches = re.findall(r'(\w+)\s*:\s*([\d,]+)', text)

        # Convert the matches to a dictionary
        data = {k: int(v.replace(',', '')) for k, v in matches}
        pokemon_info["Balls"] = data
        
        # Convert the dictionary to a JSON string
        json_data = json.dumps(pokemon_info)

        # Convert dictionary to JSON
        pokemon_json = json.dumps(pokemon_info, indent=4)
        catch_statistics.add_hunt_encounter()
        return pokemon_json
    
    def pause(self):
        catch_statistics.print_statistics()
        from instances.bot_instance import bot
        
        bot.disable_task(bot.hunting_task)
        logger.warning('[Hunting] Action Hunt is disabled.')
    
    def load_pokemon_info(self):
        with open(os.path.join(os.path.dirname(__file__), 'pokemon_info.json'), 'r') as f:
            pokemon_info_dict = json.load(f)
            return pokemon_info_dict
            
    def get_catch_result(self, pokemon_info, count, element):
        # 1. Xử lý input JSON
        if isinstance(pokemon_info, str):
            pokemon_info = json.loads(pokemon_info)

        # 2. LẤY TRỰC TIẾP TỪ SPAWN INFO (Không tra từ điển nữa)
        pokemon_name = pokemon_info.get("Name", "Unknown")
        pokemon_rarity = pokemon_info.get("Rarity", "Common").strip() # .strip() để xóa khoảng trắng thừa nếu có

        # 3. Định nghĩa màu sắc
        rarity_color = {
            'Common': Fore.WHITE, 'Uncommon': Fore.WHITE, 'Rare': Fore.WHITE,
            'Super Rare': Fore.CYAN, 'Super rare': Fore.CYAN,
            'Legendary': Fore.MAGENTA, 'Shiny': Fore.MAGENTA, 'Golden': Fore.MAGENTA
        }
        # Lấy màu tương ứng, nếu không có trong list thì mặc định là Trắng
        p_color = rarity_color.get(pokemon_rarity, Fore.WHITE)

        # 4. Kiểm tra xem có bắt được không (Dấu tích xanh ✅)
        soup = BeautifulSoup(element.get_attribute('outerHTML'), "html.parser")
        pokemon_was_catched = soup.find_all(string=lambda text: '✅' in text)

        # ---------------------------------------------------------
        if pokemon_was_catched:
            # === CHỤP ẢNH ===
            # Rarity lấy trực tiếp nên nếu là Shiny nó sẽ khớp lệnh này
            if pokemon_rarity in ['Legendary', 'Shiny', 'Golden'] and ENABLE_RUN_PICTURES:
                self.screenshot_handler.take_screenshot_by_element(element, pokemon_name, pokemon_rarity)
            
            # === XỬ LÝ SỐ TIỀN VÀ ITEM ===
            span = soup.find('span', class_=lambda value: value and 'embedFooterText' in value)
            text = span.get_text() if span else ""
            
            earned_coins_match = re.search(r'earned ([\d,]+) PokeCoins', text)
            earned_coins = int(earned_coins_match.group(1).replace(',', '')) if earned_coins_match else 0

            # Check Item
            has_item = pokemon_info.get('Item', False)
            item_received = "Unknown Item"

            if has_item:
                item_span = soup.find('span', string=lambda t: 'retrieved a' in t if t else False)
                if item_span:
                    item_received = item_span.find_next('strong').text
                
                # Log có Item
                logger.info(f"🍚 {Fore.LIGHTBLUE_EX}[{count}]{Style.RESET_ALL} {Fore.GREEN}Caught a{Style.RESET_ALL} {p_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{earned_coins} coins{Style.RESET_ALL} {Fore.GREEN}& item:{Style.RESET_ALL} {Fore.GREEN}{item_received}{Style.RESET_ALL} 🎗️")
                catch_statistics.add_catch(pokemon_rarity, earned_coins, item_received)
            else:
                # Log thường
                logger.info(f'🍚 {Fore.LIGHTBLUE_EX}[{count}]{Style.RESET_ALL} {Fore.GREEN}Caught a{Style.RESET_ALL} {p_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{earned_coins} coins{Style.RESET_ALL}')
                catch_statistics.add_catch(pokemon_rarity, earned_coins)
        
        else:
            # === TRƯỜNG HỢP BẮT HỤT ===
            logger.info(f'🍚 {Fore.LIGHTBLUE_EX}[{count}]{Style.RESET_ALL} {Fore.RED}Failed to catch a{Style.RESET_ALL} {p_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL}')
    # def get_catch_result(self, pokemon_info, count, element):
    #     if isinstance(pokemon_info, str):
    #         pokemon_info = json.loads(pokemon_info)

    #     soup = BeautifulSoup(element.get_attribute('outerHTML'), "html.parser")
    #     pokemon_was_catched = soup.find_all(string=lambda text: '✅' in text)

    #     rarity_color = {
    #         'Common': Fore.WHITE,
    #         'Uncommon': Fore.WHITE,
    #         'Rare': Fore.WHITE,
    #         'Super Rare': Fore.CYAN,
    #         'Super rare': Fore.CYAN,
    #         'Legendary': Fore.MAGENTA,
    #         'Shiny': Fore.MAGENTA,
    #         'Golden': Fore.MAGENTA
    #     }

    #     # Load the Pokemon info from the JSON file
    #     with open(os.path.join(os.path.dirname(__file__), 'pokemon_info.json'), 'r') as f:
    #         pokemon_info_from_file = json.load(f)

    #     # Check if 'Name' is in pokemon_info before trying to access it
    #     try:    
    #         if 'Name' in pokemon_info:
    #             pokemon_name = pokemon_info['Name'].lower()
    #     except Exception as e:
    #         logger.error(f"An error occurred: {e}")
        
    #     self.pokemon_info_dict = self.load_pokemon_info()

    #     if pokemon_name in self.pokemon_info_dict and 'Rarity' in self.pokemon_info_dict[pokemon_name]:
    #         pokemon_rarity = self.pokemon_info_dict[pokemon_name]['Rarity']
    #     else:
    #         print(f"{pokemon_name} not found in pokemon_info_dict or 'Rarity' not found in pokemon_info_dict[{pokemon_name}]")
    #         return
    #     # Assuming pokemon_rarity is a string like 'Common', 'Uncommon', etc.
    #     pokemon_rarity = pokemon_rarity.strip()
    #     pokemon_rarity_color = rarity_color[pokemon_rarity]
    #     has_item = pokemon_info.get('Item')
    #     color = rarity_color.get(pokemon_rarity, Fore.RESET)

    #     # Check if the Pokémon is shiny
    #     is_shiny = "Shiny" in pokemon_info.get(pokemon_name, {}).get("Rarity", "").lower()

    #     log_color = Fore.YELLOW if is_shiny else Fore.WHITE
       
    #     # Check if any element contains the ✅ emoji
    #     if pokemon_was_catched:
    #         if pokemon_rarity in ['Legendary', 'Shiny', 'Golden'] and ENABLE_RUN_PICTURES:
    #             self.screenshot_handler.take_screenshot_by_element(element, pokemon_name, pokemon_rarity)
                
    #         # Choose the log color based on the Pokemon rarity
    #         if pokemon_info["Rarity"] == "Legendary":
    #             log_color = Fore.MAGENTA
    #         elif pokemon_info["Rarity"] == "Super Rare":
    #             log_color = Fore.CYAN
    #         else:
    #             log_color = Fore.YELLOW if pokemon_info.get("Shiny", False) else Fore.WHITE

    #         span = soup.find('span', class_=lambda value: value and 'embedFooterText' in value)

    #         # Get the text of the span
    #         text = span.get_text()

    #         # Use a regular expression to find the earned coins
    #         earned_coins = re.search(r'earned ([\d,]+) PokeCoins', text)
            
    #         # Assuming earned_coins is the result of a re.match or re.search operation
    #         if earned_coins is not None:
    #             earned_coins = int(earned_coins.group(1).replace(',', ''))
    #         else:
    #             logger.error("Failed to parse earned coins.")
    #             # Handle the error appropriately, e.g., by setting a default value or raising an exception
    #             earned_coins = 0


    #         if has_item:
    #             # Looking for the span that contains the text indicating the item received
    #             item_received_span = soup.find('span', string=lambda text: 'retrieved a' in text if text else False)        

    #             # Extracting the text of the next strong tag which should contain the name of the item received
    #             if item_received_span:
    #                 item_received = item_received_span.find_next('strong').text
    #             else:
    #                 item_received = "Unknown Item"
    #             # Format the string
    #             catch_message = f"🍚 {Fore.LIGHTBLUE_EX}[{count}]{Style.RESET_ALL} {Fore.GREEN}Caught a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{earned_coins} Pokecoins{Style.RESET_ALL} {Fore.GREEN}and a{Style.RESET_ALL} {Fore.GREEN}{item_received}{Style.RESET_ALL} 🎗️"

    #             # Log the message
    #             logger.info(catch_message)
    #             catch_statistics.add_catch(pokemon_rarity, earned_coins, item_received)
    #             return
            
    #         # Print the Pokemon name, rarity, and earned coins in one line
    #         if pokemon_rarity == "Shiny":
    #             logger.info(f'🍚 {Fore.LIGHTBLUE_EX}[{count}]{Style.RESET_ALL} {Fore.GREEN}Caught a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{earned_coins} Pokecoins{Style.RESET_ALL}')
    #         else:
    #             logger.info(f'🍚 {Fore.LIGHTBLUE_EX}[{count}]{Style.RESET_ALL} {Fore.GREEN}Caught a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL} {Fore.GREEN}with{Style.RESET_ALL} {Fore.YELLOW}{earned_coins} Pokecoins{Style.RESET_ALL}')
            
    #         catch_statistics.add_catch(pokemon_rarity, earned_coins)
    #     else:
    #         logger.info(f'🍚 {Fore.LIGHTBLUE_EX}[{count}]{Style.RESET_ALL} {Fore.RED}Failed to catch a{Style.RESET_ALL} {pokemon_rarity_color}{pokemon_rarity} {pokemon_name}{Style.RESET_ALL}')