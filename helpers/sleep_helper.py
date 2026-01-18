import time
import msvcrt
from logger import Logger
from catch_statistics import CatchStatistics
logger = Logger().get_logger()
catch_statistics = CatchStatistics()

# from bot_instance import bot, logger, catch_statistics

def pause_execution():
    logger.warning('Execution paused. Press enter to continue...')
    input("")
    logger.info('Execution resumed...')
    # Sleep 3 seconds to avoid double key press
    time.sleep(1.5)

def show_statistics_execution():
    logger.warning('Execution paused. Press enter to continue...')
    
    catch_statistics.print_statistics()
    
    input("")
    logger.info('Execution resumed...')
    # Sleep 3 seconds to avoid double key press
    time.sleep(1.5)
    return

def switch_task_command(task, task_name):
    from instances.bot_instance import bot
    is_enabled = task.enabled
    message = 'ENABLED'  # Default value
    if is_enabled:
        message = 'DISABLED'
    logger.warning(f'[TASKS] Switching {task_name} task to {message}...')
    logger.warning('[TASKS] Execution paused. Press enter to continue...')
    bot.switch_task(task)
    input("")
    logger.info('Execution resumed...')
    time.sleep(1.5)

# --- SỬA HÀM NÀY ---
def trigger_send_coins():
    # 1. Import thêm 'driver' trực tiếp từ bot_instance (thay vì lấy bot.driver)
    from instances.bot_instance import driver, settings 
    from commands.send import Send
    
    # 2. Truyền 'driver' vào class Send
    sender = Send(driver, settings)
    sender.start()
    
    time.sleep(1.5)
# -------------------
def interruptible_sleep(sleep_time):
    from instances.bot_instance import bot

    # Map keys to functions and their parameters
    commands = {
        'p': (pause_execution, ),
        'P': (pause_execution, ),
        's': (show_statistics_execution, ),
        'S': (show_statistics_execution, ),
        'h': (switch_task_command, bot.hunting_task, 'hunting'),
        'H': (switch_task_command, bot.hunting_task, 'hunting'),
        'f': (switch_task_command, bot.fishing_task, 'fishing'),
        'F': (switch_task_command, bot.fishing_task, 'fishing'),
        'b': (switch_task_command, bot.battle_task, 'battle'),
        'B': (switch_task_command, bot.battle_task, 'battle'),
        'e': (switch_task_command, bot.explore_task, 'explore'),
        'E': (switch_task_command, bot.explore_task, 'explore'),
        'g': (trigger_send_coins, ),
        'G': (trigger_send_coins, ),
    }

    start_time = time.time()
    while time.time() - start_time < sleep_time:
        time.sleep(0.1)  # Check every 0.1 seconds
        if msvcrt.kbhit():
            key_pressed = msvcrt.getch().decode('utf-8')
            if key_pressed in commands:
                func, *params = commands[key_pressed]
                func(*params)  # Call the corresponding function with its parameters