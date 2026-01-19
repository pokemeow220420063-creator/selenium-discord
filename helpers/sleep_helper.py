import asyncio
import time
import sys
from logger import Logger
from catch_statistics import CatchStatistics
from colorama import Fore, Style

# Kiểm tra hệ điều hành để import msvcrt (Chỉ Windows mới có)
try:
    import msvcrt
except ImportError:
    msvcrt = None

logger = Logger().get_logger()
catch_statistics = CatchStatistics()

# ====================================================
# CÁC HÀM XỬ LÝ LỆNH (Đã chuyển sang Async)
# ====================================================

async def pause_execution():
    """Tạm dừng bot nhưng không làm mất kết nối"""
    logger.warning(f'{Fore.YELLOW}Execution paused. Press Enter to continue...{Style.RESET_ALL}')
    
    # Chạy hàm input() trong thread riêng để không chặn luồng Async của Bot
    await asyncio.to_thread(input, "")
    
    logger.info(f'{Fore.GREEN}Execution resumed...{Style.RESET_ALL}')
    await asyncio.sleep(1.5)

async def show_statistics_execution():
    """Hiển thị thống kê"""
    logger.warning(f'{Fore.YELLOW}Paused for Statistics. Press Enter to continue...{Style.RESET_ALL}')
    
    catch_statistics.print_statistics()
    
    await asyncio.to_thread(input, "")
    logger.info(f'{Fore.GREEN}Execution resumed...{Style.RESET_ALL}')
    await asyncio.sleep(1.5)

async def switch_task_command(bot, task_name, display_name):
    """Bật/Tắt task"""
    task = getattr(bot, task_name, None)
    if not task:
        logger.error(f"Task {task_name} not found!")
        return

    is_enabled = task.enabled
    status = f"{Fore.RED}DISABLED{Style.RESET_ALL}" if is_enabled else f"{Fore.GREEN}ENABLED{Style.RESET_ALL}"
    
    logger.warning(f'[TASKS] Switching {display_name} task to {status}...')
    
    # Thực hiện switch
    bot.switch_task(task)
    
    await asyncio.sleep(1.0)
    logger.info(f'[TASKS] {display_name} is now {status}. Resuming...')

async def trigger_send_coins(bot):
    """Gửi coin (Yêu cầu module Send đã được port sang Async)"""
    # Import cục bộ để tránh circular import nếu chưa cần
    try:
        from commands.send import Send
        # Khởi tạo Send với driver và settings từ bot
        sender = Send(bot.driver, bot.settings)
        await sender.start() # Giả sử Send.start() đã là async
    except ImportError:
        logger.error("Module 'commands.send' not found.")
    except Exception as e:
        logger.error(f"Error triggering send coins: {e}")
    
    await asyncio.sleep(1.5)

# ====================================================
# HÀM CHÍNH: INTERRUPTIBLE SLEEP (ASYNC)
# ====================================================

async def interruptible_sleep(bot, duration):
    """
    Ngủ trong khoảng thời gian `duration` (giây).
    Trong lúc ngủ vẫn check phím bấm để điều khiển Bot.
    
    Args:
        bot: Đối tượng Bot (được truyền vào để tránh import vòng vo)
        duration: Thời gian ngủ (giây)
    """
    if duration <= 0: return

    # Map phím tắt -> Hàm xử lý
    # Lưu ý: Các hàm này đều phải là async hoặc được await
    commands = {
        'p': (pause_execution, []),
        's': (show_statistics_execution, []),
        'h': (switch_task_command, [bot, 'hunting_task', 'HUNTING']),
        'f': (switch_task_command, [bot, 'fishing_task', 'FISHING']),
        'b': (switch_task_command, [bot, 'battle_task', 'BATTLE']),
        'e': (switch_task_command, [bot, 'explore_task', 'EXPLORE']),
        'c': (switch_task_command, [bot, 'catchbot_task', 'CATCHBOT']),
        'g': (trigger_send_coins, [bot]),
    }

    start_time = time.time()
    
    while (time.time() - start_time) < duration:
        # 1. Kiểm tra phím bấm (Non-blocking trên Windows)
        if msvcrt and msvcrt.kbhit():
            try:
                key_pressed = msvcrt.getch().decode('utf-8').lower()
                
                if key_pressed in commands:
                    func, args = commands[key_pressed]
                    # Gọi hàm async
                    await func(*args)
                    
                    # Sau khi xử lý lệnh, trừ đi thời gian đã trôi qua để ngủ tiếp (hoặc reset tùy logic)
                    # Ở đây ta cứ để vòng lặp tiếp tục check time
            except UnicodeDecodeError:
                pass # Bỏ qua phím lạ

        # 2. Quan trọng: Nhường thread cho Bot giữ kết nối Discord
        # Check mỗi 0.1s. Nếu sleep quá lâu ở đây thì phím bấm sẽ bị delay.
        await asyncio.sleep(0.1)