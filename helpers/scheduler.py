import asyncio
import time
import random
from logger import Logger
from colorama import Fore, Style

logger = Logger().get_logger()

class Task:
    def __init__(self, func, interval_func):
        self.func = func  # Hàm này bây giờ sẽ trả về một coroutine (Async)
        self.interval_func = interval_func
        self.last_run = 0
        self.enabled = True 

    # Đổi thành Async để await hàm func()
    async def run(self):
        if self.enabled: 
            # Gọi hàm async và chờ nó xong
            await self.func()
            self.last_run = time.time()

    def should_run(self):
        # Logic check thời gian giữ nguyên
        interval = self.interval_func() if callable(self.interval_func) else self.interval_func
        return self.enabled and (time.time() - self.last_run) > interval

    def enable(self): self.enabled = True
    def disable(self): self.enabled = False

class Scheduler:
    def __init__(self):
        self.tasks = []
        # Không dùng threading.Lock nữa vì asyncio chạy đơn luồng (single-threaded) an toàn

    def add_task(self, task):
        self.tasks.append(task)

    # Đổi run() thành async run()
    async def run(self):
        logger.info(f"{Fore.GREEN}[Scheduler] Started Async Grinder Mode (No Sleep - 24/7).{Style.RESET_ALL}")

        current_fatigue = 0.0
        
        while True:
            # --- LOGIC MODE (BURST/CHILL) GIỮ NGUYÊN ---
            is_burst_mode = random.random() < 0.25
            if is_burst_mode:
                work_minutes = random.uniform(10, 20)
                logger.info(f"{Fore.RED}[Scheduler] BURST MODE! Farming fast for {int(work_minutes)}m.{Style.RESET_ALL}")
            else:
                work_minutes = max(15, min(60, random.gauss(30, 10)))
                logger.info(f"{Fore.CYAN}[Scheduler] Chill Mode. Farming for ~{int(work_minutes)}m.{Style.RESET_ALL}")

            if current_fatigue > 0.8:
                work_minutes *= 0.7

            end_work_time = time.time() + (work_minutes * 60)
            
            # --- VÒNG LẶP FARMING (Async) ---
            while time.time() < end_work_time:
                
                # [Anti-Ban] Micro-break (Thay time.sleep bằng asyncio.sleep)
                distraction_chance = 0.01 if is_burst_mode else 0.05
                if random.random() < distraction_chance:
                    await asyncio.sleep(random.uniform(5, 15))

                task_executed = False
                
                # Duyệt qua các Task
                for task in self.tasks:
                    if task.should_run():
                        # Hesitation (Độ trễ phản hồi)
                        hesitation = random.uniform(0.1, 0.8) if is_burst_mode else random.uniform(1.5, 3.5)
                        await asyncio.sleep(hesitation)
                        
                        try:
                            # Chạy Task (await)
                            await task.run()
                            task_executed = True
                        except Exception as e:
                            logger.error(f"Task Error: {e}")

                # Idle time nếu không có task nào chạy
                if not task_executed:
                    wait_time = 0.5 if is_burst_mode else 1.0
                    await asyncio.sleep(wait_time)

            # --- NGHỈ GIẢI LAO (BREAK) ---
            fatigue_gain = (work_minutes / 60) * (1.2 if is_burst_mode else 0.8)
            current_fatigue = min(1.0, current_fatigue + fatigue_gain)
            
            base_break = random.uniform(1, 5)
            actual_break = base_break + (current_fatigue * 5)
            
            if random.random() < 0.02:
                actual_break = random.uniform(10, 15)
                current_fatigue = 0.0 
                logger.info(f"{Fore.MAGENTA}[Scheduler] Quick Snack Break ({int(actual_break)}m).{Style.RESET_ALL}")
            else:
                current_fatigue = max(0.0, current_fatigue - 0.2)

            logger.warning(
                f"{Fore.BLUE}[Scheduler] Short Rest: {Fore.YELLOW}{int(actual_break)}{Fore.BLUE}m "
                f"(Fatigue: {int(current_fatigue*100)}%){Style.RESET_ALL}"
            )
            
            # Quan trọng: Dùng asyncio.sleep để không chặn kết nối Discord
            await asyncio.sleep(actual_break * 60)
            
            logger.info(f"{Fore.GREEN}[Scheduler] Ready! Resume farming.{Style.RESET_ALL}")