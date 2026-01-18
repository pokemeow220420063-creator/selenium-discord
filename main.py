from instances.bot_instance import bot, logger, driver, catch_statistics, settings
import os
from helpers.sleep_helper import interruptible_sleep
import threading
import sys
bat_file_name = None



def try_login(driver):
    if len(sys.argv) > 1:
        bat_file_name = [sys.argv[1]]
    
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    channel = os.getenv('CHANNEL')
    discord_token = os.getenv('DISCORD_TOKEN')

    driver.start_driver()
    #  check if discord_token is valid
    if discord_token and len(discord_token) > 25:
        if not driver.inject_token(discord_token):
            driver.navigate_to_page("https://discord.com/login")
            driver.login(email,password) 
    else:
        driver.navigate_to_page("https://discord.com/login")
        driver.login(email,password)
    driver.navigate_to_page(channel)
    interruptible_sleep(5)
    
     
if __name__ == "__main__":
    from license_guard import verify_license
    verify_license(interactive=True)
    try_login(driver)
    driver.validate()
    driver.print_initial_message()
    threading.Thread(target=bot.scheduler.run).start()
