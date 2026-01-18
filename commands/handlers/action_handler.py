from driver import Driver
from validators.action import Action
from selenium.webdriver.remote.webelement import WebElement
from helpers.sleep_helper import interruptible_sleep
from time import sleep
from catch_statistics import CatchStatistics
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

catch_statistics = CatchStatistics()

class ActionHandler:
    def __init__(self):
        self.action_handlers = {
            Action.RETRY: self.retry,
            Action.SOLVE_CAPTCHA: self.solve_captcha,
            Action.PAUSE: self.pause,
            Action.CATCH_AGAIN: self.catch_again,
            Action.SKIP: self.skip,
            Action.REFRESH: self.refresh
        }
        self.command = None
    
    def start(self, command):
        raise NotImplementedError


    def handle_action(self, action, driver=None, element=None):
        # Manage refresh action
        if action == Action.REFRESH and driver is not None and element is not None:
            self.action_handlers[action](driver, element)
        elif action == Action.SOLVE_CAPTCHA and driver is not None and element is not None:
            self.action_handlers[action](driver, element)
        else:
            self.action_handlers[action]()

    def retry(self):
        self.start(self.command)

    def solve_captcha(self, driver: Driver, element: WebElement):
        driver.solve_captcha(element)
        interruptible_sleep(3)
        self.start(self.command)

    def pause(self):
        catch_statistics.print_statistics()
        # sleep(60*60*24)
        input("")
    def catch_again(self):
        interruptible_sleep(3)
        self.start(self.command)
        
    def skip(self):
        raise NotImplementedError

    
    def refresh(self, driver: Driver, element: WebElement):
        driver.refresh()
        last_element = driver.get_last_message_from_user("PokéMeow")
        if "A wild Captcha appeared!" in last_element.text:
            self.solve_captcha(driver, last_element)
        else:
            interruptible_sleep(8)
    