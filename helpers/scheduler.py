import threading
import time
import random
from helpers.sleep_helper import interruptible_sleep
from logger import Logger
from colorama import Fore, Style
# Khởi tạo logger để in thông báo màu mè cho đẹp
logger = Logger().get_logger()

class Task:
    def __init__(self, func, interval_func):
        self.func = func
        self.interval_func = interval_func
        self.last_run = 0
        self.enabled = True 

    def start(self):
        if self.enabled: 
            self.func()
            self.last_run = time.time()

    def should_run(self):
        # Kiểm tra xem đã đến lúc chạy chưa (dựa trên interval_func)
        interval = self.interval_func() if callable(self.interval_func) else self.interval_func
        return self.enabled and (time.time() - self.last_run) > interval

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

class Scheduler:
    def __init__(self):
        self.tasks = []
        self.lock = threading.Lock()

    def add_task(self, task):
        with self.lock:
            self.tasks.append(task)

    def remove_task(self, task):
        with self.lock:
            self.tasks.remove(task)

    def run(self):
        """
        Hardcore Human-like Scheduler:
        - KHÔNG NGỦ ĐÊM (No Sleep).
        - Vẫn giữ Burst Mode (lúc nhanh lúc chậm).
        - Reaction time biến thiên liên tục.
        """
        logger.info(f"{Fore.GREEN}[Scheduler] Started Hardcore Grinder Mode (No Sleep - 24/7).{Style.RESET_ALL}")

        current_fatigue = 0.0
        
        while True:
            # ========================================================
            # 1. CHỌN CHẾ ĐỘ: CÀY BÌNH THƯỜNG HAY "HĂNG MÁU"
            # ========================================================
            
            # 25% cơ hội vào "Burst Mode": Gõ cực nhanh, ít nghỉ (như lúc đang có Event)
            is_burst_mode = random.random() < 0.25
            
            if is_burst_mode:
                # Burst: Làm ngắn (10-20p) nhưng tốc độ cao
                work_minutes = random.uniform(10, 20)
                logger.info(f"{Fore.RED}[Scheduler] BURST MODE! Farming fast for {int(work_minutes)}m.{Style.RESET_ALL}")
            else:
                # Chill: Làm dài (20-50p) tốc độ tàn tàn
                # Dùng Gaussian để thời gian làm việc tự nhiên (quanh mốc 30p)
                work_minutes = max(15, min(60, random.gauss(30, 10)))
                logger.info(f"{Fore.CYAN}[Scheduler] Chill Mode. Farming for ~{int(work_minutes)}m.{Style.RESET_ALL}")

            # Nếu mệt quá (>80%) thì giảm thời gian làm việc lại một chút để đi nghỉ sớm
            if current_fatigue > 0.8:
                work_minutes *= 0.7

            end_work_time = time.time() + (work_minutes * 60)
            
            # ========================================================
            # 2. VÒNG LẶP FARMING (WORK LOOP)
            # ========================================================
            while time.time() < end_work_time:
                
                # [Anti-Ban] Micro-break (Lơ đễnh nhẹ)
                # Burst mode thì tập trung hơn (ít lơ đễnh hơn)
                distraction_chance = 0.01 if is_burst_mode else 0.05
                
                if random.random() < distraction_chance:
                    # Dừng 5s - 15s (Check tin nhắn/Uống nước)
                    interruptible_sleep(random.uniform(5, 15))

                task_executed = False
                with self.lock:
                    for task in self.tasks:
                        if task.should_run():
                            # [QUAN TRỌNG] ĐỘ TRỄ PHẢN HỒI (Hesitation)
                            # Đây là cái giúp bạn KHÔNG bị ban dù chạy 24/7
                            if is_burst_mode:
                                # Hăng máu: Gõ nhanh (0.1s - 0.8s)
                                hesitation = random.uniform(0.1, 0.8)
                            else:
                                # Bình thường: Gõ từ tốn (1.5s - 3.5s) -> Rất an toàn
                                hesitation = random.uniform(1.5, 3.5)
                            
                            interruptible_sleep(hesitation)
                            
                            try:
                                task.start()
                                task_executed = True
                            except Exception as e:
                                logger.error(f"Error: {e}")

                # Thời gian chờ sau khi quét hết task (Idle time)
                if not task_executed:
                    if is_burst_mode:
                         interruptible_sleep(0.5) # Quét lại nhanh
                    else:
                         interruptible_sleep(1.0) # Quét lại chậm

            # ========================================================
            # 3. NGHỈ GIẢI LAO (BREAK) - NGẮN GỌN
            # ========================================================
            
            # Tính độ mệt
            fatigue_gain = (work_minutes / 60) * (1.2 if is_burst_mode else 0.8)
            current_fatigue = min(1.0, current_fatigue + fatigue_gain)
            
            # Nghỉ cơ bản rất ngắn: 1 đến 5 phút
            base_break = random.uniform(1, 5)
            
            # Cộng thêm chút xíu theo độ mệt (max thêm 5 phút nữa)
            actual_break = base_break + (current_fatigue * 5)
            
            # Rất hiếm khi (2%) nghỉ lâu hơn xíu (10-15p) để đi vệ sinh/ăn nhanh
            if random.random() < 0.02:
                actual_break = random.uniform(10, 15)
                current_fatigue = 0.0 # Reset mệt mỏi sau khi nghỉ "dài"
                logger.info(f"{Fore.MAGENTA}[Scheduler] Quick Snack Break ({int(actual_break)}m).{Style.RESET_ALL}")
            else:
                # Giảm mệt từ từ
                current_fatigue = max(0.0, current_fatigue - 0.2)

            logger.warning(
                f"{Fore.BLUE}[Scheduler] Short Rest: {Fore.YELLOW}{int(actual_break)}{Fore.BLUE}m "
                f"(Fatigue: {int(current_fatigue*100)}%){Style.RESET_ALL}"
            )
            
            interruptible_sleep(actual_break * 60)
            
            # Tỉnh dậy là làm luôn, không lờ đờ nữa
            logger.info(f"{Fore.GREEN}[Scheduler] Ready! Resume farming.{Style.RESET_ALL}")
