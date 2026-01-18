from bot import Bot
from catch_statistics import CatchStatistics
from driver import Driver
from settings import Settings
from logger import Logger

settings = Settings()
logger = Logger().get_logger()
catch_statistics = CatchStatistics()
driver = Driver(settings.driver_path)
bot = Bot(driver)