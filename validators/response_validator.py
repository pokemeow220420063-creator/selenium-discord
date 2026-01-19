from logger import Logger
from validators.action import Action
# Lưu ý: API dùng asyncio.sleep, nhưng validator chỉ return Action nên không cần sleep ở đây
# Việc sleep sẽ do ActionHandler lo để đảm bảo non-blocking

logger = Logger().get_logger()

def evaluate_response(message) -> str:
    # message: Là object tin nhắn của Discord (discord.Message)
    
    # Trường hợp không thấy tin nhắn (Lag/Mất mạng)
    if message is None:
        # Giữ nguyên log cũ dù API không refresh trang
        logger.error('No response from PokéMeow, refreshing page...') 
        return Action.REFRESH
    
    content = message.content # Lấy nội dung tin nhắn
    
    if "A wild Captcha appeared!" in content:
        logger.warning('A wild Captcha appeared!')
        return Action.SOLVE_CAPTCHA
        
    if "Please wait" in content:
        logger.info('Please wait...')
        # interruptible_sleep(1.5) -> Đã chuyển sang Handler xử lý
        return Action.RETRY
    
    if "Please catch the" in content:
        logger.error('Please catch the Pokemon you spawned first!')
        return Action.CATCH_AGAIN
    
    if "You can now catch" in content:
        logger.info('You can now catch Pokemon again.')
        # interruptible_sleep(3) -> Đã chuyển sang Handler xử lý
        return Action.RETRY
    
    if "Not even a nibble" in content:
        logger.info('🎣 [ESCAPED!] Not even a nibble...')
        return Action.SKIP
    
    if "reached your daily catch" in content:
        # Giữ nguyên 3 dòng log như code cũ
        logger.warning('You reached your daily catch limit. Stopping the bot...')
        logger.warning('You reached your daily catch limit. Stopping the bot...')
        logger.warning('You reached your daily catch limit. Stopping the bot...')
        return Action.PAUSE
    
    if "have reached the daily" in content:
        # Giữ nguyên 3 dòng log như code cũ
        logger.warning('You reached your daily catch limit. Stopping the bot...')
        logger.warning('You reached your daily catch limit. Stopping the bot...')
        logger.warning('You reached your daily catch limit. Stopping the bot...')
        return Action.PAUSE
       
    return Action.PROCEED