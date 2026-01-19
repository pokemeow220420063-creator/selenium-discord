import asyncio
import discord
from functools import wraps
from discord.errors import HTTPException, Forbidden, NotFound, DiscordServerError
from logger import Logger

# Khoi tao logger
logger = Logger().get_logger()

def handle_on_start_exceptions(max_retries=3):
    """
    Decorator xu ly cac loi mang khi goi API Discord.
    Tu dong retry khi gap Rate Limit hoac loi Server.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            
            for attempt in range(max_retries):
                try:
                    # Co gang thuc hien hanh dong
                    return await func(*args, **kwargs)

                # === LOI HTTP TU DISCORD ===
                except HTTPException as e:
                    # 429: Rate Limit (Spam qua nhanh)
                    if e.status == 429:
                        wait_time = e.retry_after + 0.5
                        logger.warning(f"[API] Rate Limit (429). Sleeping for {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        continue 
                    
                    # 5xx: Server Discord loi
                    if 500 <= e.status < 600:
                        logger.error(f"[API] Discord Server Error ({e.status}). Retrying in 5s...")
                        await asyncio.sleep(5)
                        continue

                    # 403: Khong co quyen
                    if e.status == 403:
                        logger.critical(f"[API] FORBIDDEN (403): Bot missing permissions.")
                        return None 
                    
                    # 404: Khong tim thay
                    if e.status == 404:
                        logger.error(f"[API] NOT FOUND (404): Target does not exist.")
                        return None

                    # Loi HTTP khac
                    logger.error(f"[API] HTTP Error {e.status}: {e.text}")
                    return None

                # === LOI MANG (TIMEOUT) ===
                except (asyncio.TimeoutError, TimeoutError):
                    logger.warning(f"[API] Network Timeout. Retrying ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(2)
                    continue
                
                # === LOI SERVER NOI BO DISCORD ===
                except DiscordServerError:
                    logger.error("[API] Discord Internal Server Error. Retrying in 5s...")
                    await asyncio.sleep(5)
                    continue

                # === LOI KHAC (BUG CODE) ===
                except Exception as e:
                    logger.error(f"[API] Unexpected Error in '{func.__name__}': {e}")
                    import traceback
                    traceback.print_exc()
                    return None

            # Neu het so lan thu ma van loi
            logger.error(f"[API] Action '{func.__name__}' failed after {max_retries} attempts.")
            return None

        return wrapper
    return decorator