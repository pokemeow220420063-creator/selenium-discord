from logger import Logger
logger = Logger().get_logger()
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helpers.sleep_helper import interruptible_sleep
import time
import traceback

def handle_on_start_exceptions(func):
    def wrapper(*args, **kwargs):
        self = args[0]  # Get the 'self' reference from the first argument
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"An error occurred in {func.__name__}: {e}")
            traceback.print_exc()  # Print the full stack trace
            safely_refresh_page(self)
            process_game_state(self)
    return wrapper

def safely_refresh_page(self):
    """Refresh the page and wait for a specific element that signifies the page is ready."""
    try:
        self.driver.driver.refresh()
        # Wait for the element to be visible, not just present
        element_locator = (By.XPATH, "//span[contains(@class, 'emptyText')]")
        WebDriverWait(self.driver.driver, 15).until(EC.visibility_of_element_located(element_locator))
    except Exception as e:
        logger.error(f"Failed to refresh the page and find element: {e}")

def process_game_state(self, retry_count=0):
    """Check for specific game conditions and act accordingly."""
    max_retries = 3
    try:
        time.sleep(1.5)  # Short delay to ensure stability
        element_locator = (By.XPATH, "//span[contains(@class, 'emptyText')]")
        WebDriverWait(self.driver.driver, 15).until(EC.visibility_of_element_located(element_locator))
        
        pokemeow_message = self.driver.get_last_message_from_user("PokéMeow")
        if pokemeow_message and "A wild Captcha appeared!" in pokemeow_message.text:
            logger.warning('A wild Captcha appeared!')
            self.driver.solve_captcha(pokemeow_message)
        elif pokemeow_message:
            logger.info('Continuing game play...')
            interruptible_sleep(8)
            # self.start(self.command)
        else:
            if retry_count < max_retries:
                logger.error('[process_game_state] No PokéMeow message found. Retrying...')
                process_game_state(self, retry_count + 1)
            else:
                logger.error('[process_game_state] No PokéMeow message found after maximum retries.')
    except Exception as e:
        if retry_count < max_retries:
            logger.error(f"[process_game_state] Error processing game state: {e}. Retrying...")
            process_game_state(self, retry_count + 1)
        else:
            logger.error(f"[process_game_state] Error processing game state after maximum retries: {e}")


