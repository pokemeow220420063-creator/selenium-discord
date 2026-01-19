import asyncio
import re
from logger import Logger
from captcha_service import CaptchaService
from colorama import Fore, Style

logger = Logger().get_logger()

class Driver:
    def __init__(self, bot, channel):
        self.bot = bot
        self.channel = channel
        self.pokemeow_id = 664508672713424926
        self.captcha_service = CaptchaService()
        self.last_message_cache = None # Lưu tạm tin nhắn để xử lý

    # ==========================================
    # 1. CORE FUNCTIONS (Tương tác cơ bản)
    # ==========================================

    async def write(self, content):
        """Gửi lệnh/tin nhắn"""
        await self.channel.send(content)

    async def get_last_message_from_user(self, username="PokéMeow"):
        """Lấy tin nhắn cuối trong lịch sử (check logs, inv, captcha)"""
        try:
            # Lấy 3 tin gần nhất cho chắc
            async for message in self.channel.history(limit=3):
                if message.author.id == self.pokemeow_id:
                    self.last_message_cache = message
                    return message
        except Exception as e:
            logger.error(f"[Driver] History error: {e}")
        return None

    async def get_last_element_by_user(self, username="PokéMeow", timeout=10):
        """Chờ tin nhắn MỚI phản hồi (Quest, Catch, Battle)"""
        def check(m):
            return m.author.id == self.pokemeow_id and m.channel.id == self.channel.id

        try:
            message = await self.bot.wait_for('message', check=check, timeout=timeout)
            self.last_message_cache = message
            return message
        except asyncio.TimeoutError:
            return None

    async def check_for_new_message(self):
        """(Alias) Kiểm tra tin nhắn mới"""
        return await self.get_last_message_from_user()

    async def wait_next_message(self, timeout=10):
        """(Alias) Chờ tin nhắn tiếp theo"""
        return await self.get_last_element_by_user(timeout=timeout)

    # ==========================================
    # 2. VALIDATION & CAPTCHA (Hàm bạn yêu cầu)
    # ==========================================

    async def validate(self):
        """
        Kiểm tra xem có Captcha xuất hiện không.
        Được gọi trước các hành động quan trọng để đảm bảo an toàn.
        """
        # 1. Lấy tin nhắn cuối (Async)
        pokemeow_last_message = await self.get_last_message_from_user("PokéMeow")
        
        if pokemeow_last_message is None:
            return
        
        # 2. Kiểm tra nội dung (.content thay vì .text)
        if "A wild Captcha appeared!" in pokemeow_last_message.content:
            logger.warning('Captcha detected via Validate!')
            # 3. Giải Captcha (Async)
            await self.solve_captcha(pokemeow_last_message)

    async def get_captcha(self):
        """Lấy URL ảnh Captcha từ tin nhắn cache"""
        msg = await self.get_last_message_from_user()
        if not msg: return None
        if msg.attachments: return msg.attachments[0].url
        if msg.embeds and msg.embeds[0].image: return msg.embeds[0].image.url
        return None

    async def solve_captcha(self, message=None):
        """Logic giải Captcha: Tải ảnh -> Gửi API -> Nhập kq -> Chờ confirm"""
        logger.warning("🚨 PROCESSING CAPTCHA...")
        if not message:
            message = await self.get_last_message_from_user()

        image_url = await self.get_captcha()
        if not image_url: 
            logger.error("Captcha found but no image!")
            return

        # Chạy trong thread để không chặn bot
        img_path = await asyncio.to_thread(self.captcha_service.download_captcha, image_url)
        number = await asyncio.to_thread(self.captcha_service.send_image, img_path)

        if number:
            logger.info(f"🔢 Solved: {number}")
            await asyncio.sleep(4)
            await self.write(str(number))
            # Chờ xem bot trả lời gì (đúng/sai)
            await self.wait_for_element_text_to_change(timeout=10)

    # ==========================================
    # 3. INTERACTION (Click & Text Change)
    # ==========================================

    async def click_next_button(self):
        """Bấm nút Next trong Inventory"""
        msg = self.last_message_cache or await self.get_last_message_from_user()
        if not msg or not msg.components: return False

        for row in msg.components:
            for component in row.children:
                if "next" in str(component.custom_id).lower():
                    try:
                        await component.click()
                        return True
                    except: return False
        return False

    async def click_on_ball(self, ball_name="pokeball"):
        """Bấm nút chọn bóng khi bắt Pokemon"""
        msg = await self.get_last_message_from_user()
        if not msg or not msg.components: return

        for row in msg.components:
            for component in row.children:
                # So sánh tên bóng với label hoặc id
                c_label = str(component.label).lower() if component.label else ""
                c_id = str(component.custom_id).lower() if component.custom_id else ""
                
                if ball_name.lower() in c_label or ball_name.lower() in c_id:
                    await component.click()
                    return

    async def wait_for_element_text_to_change(self, element=None, timeout=10):
        """Chờ tin nhắn bị chỉnh sửa (Edit)"""
        target_id = element.id if element else (self.last_message_cache.id if self.last_message_cache else None)
        if not target_id: return None

        def check(before, after):
            return before.id == target_id

        try:
            _, after = await self.bot.wait_for('message_edit', check=check, timeout=timeout)
            self.last_message_cache = after
            return after
        except asyncio.TimeoutError:
            return None

    # ==========================================
    # 4. GAME LOGIC STUBS (Hàm cũ)
    # ==========================================

    def get_next_ball(self, current_ball):
        """
        Logic hạ cấp bóng: Master -> Premier -> Ultra -> Great -> Poke -> None.
        Hàm này xử lý logic thuần túy nên không cần async/await.
        """
        balls_priority = {
            "masterball": 5,
            "premierball": 4,
            "ultraball": 3,
            "greatball": 2,
            "pokeball": 1
        }

        # Lấy độ ưu tiên hiện tại
        current_priority = balls_priority.get(current_ball)

        # Nếu không tìm thấy bóng hoặc đang là Pokeball (thấp nhất) -> Hết đường lùi
        if current_priority is None or current_priority == 1:
            return None

        # Tìm bóng có độ ưu tiên thấp hơn kế tiếp
        # Sắp xếp giảm dần: 5, 4, 3, 2, 1
        for ball, priority in sorted(balls_priority.items(), key=lambda item: item[1], reverse=True):
            if priority < current_priority:
                return ball
        
        return None

    async def buy_balls(self, inventory):
        """
        Tự động mua bóng dựa trên số tiền hiện có.
        """
        await asyncio.sleep(5) # Thay interruptible_sleep
        
        budget = 0

        # Tìm số dư Pokecoin trong inventory
        for item in inventory:
            if item["name"] == "pokecoin":
                budget = item["count"]
                # Giới hạn budget 200k như code cũ
                if budget > 200000:
                    budget = 200000
                break
            
        # Tạo danh sách lệnh mua từ class Shop
        # Giả sử Shop.generate_purchase_commands là hàm đồng bộ (không cần await)
        commands = Shop.generate_purchase_commands(budget)
        
        if not commands:
            logger.info("❌ Not enough budget to buy balls.")
            return
        
        # Gửi lệnh mua
        for command in commands:
            logger.info(f'💰 {command}')
            await self.write(command) # Gửi lệnh async
            await asyncio.sleep(5.5) # Chờ 5.5s giữa các lần mua

    def print_initial_message(self):
        logger.warning(f"{Fore.GREEN}Autplay Settings:{Style.RESET_ALL}")
        logger.warning("[Autplay settings] AutoBuy enabled: " + str(ENABLE_AUTO_BUY_BALLS))
        logger.warning("[Autplay settings] AutoLootbox enabled: " + str(ENABLE_AUTO_LOOTBOX))
        logger.warning("[Autplay settings] AutoRelease enabled: " + str(ENABLE_RELEASE_DUPLICATES))
        logger.warning("[Autplay settings] AutoQuestReroll enabled: " + str(ENABLE_AUTO_QUEST_REROLL))
        logger.warning("[Autplay settings] AutoEgg enabled: " + str(ENABLE_AUTO_EGG_HATCH))
        logger.warning("[Autplay settings] [FISHING] enabled: " + str(ENABLE_FISHING))
        logger.warning("[Autplay settings] [BATTLE] enabled: " + str(ENABLE_BATTLE_NPC))
        logger.warning("[Autplay settings] [HUNTING] enabled: " + str(ENABLE_HUNTING))
        logger.warning("[Autplay settings] RunPictures enabled: " + str(ENABLE_RUN_PICTURES))
        logger.warning(f"{Fore.GREEN}Autplay Advice:{Style.RESET_ALL}")
        logger.warning("[Autplay Advice] you can pause the bot by pressing 'p' in the console")
        logger.warning("[Autplay Advice] you can see statistics by pressing 's' in the console")
        logger.warning("[Autplay Advice] you can resume the bot by pressing 'enter' in the console")
        logger.warning("[Autplay Advice] you can stop the bot by pressing 'ctrl + c' in the console")
        logger.warning("[Autplay Advice] you ENABLE/DISABLE [BATTLE] by pressing 'b' in the console")
        logger.warning("[Autplay Advice] you ENABLE/DISABLE [FISHING] by pressing 'f' in the console")
        logger.warning("[Autplay Advice] you ENABLE/DISABLE [HUNTING] by pressing 'h' in the console")
        logger.warning(f"[Autplay Advice] you ENABLE/DISABLE [EXPLORE] by pressing 'e' in the console {Fore.RED}(Only for Pokémeow patreons!){Style.RESET_ALL}")
        logger.warning(f"{Fore.GREEN}Config.ini Settings:{Style.RESET_ALL}")
        logger.warning('[config.ini] Default ball for Fishing: %s', fishing_ball)
        logger.warning('[config.ini] Default ball for Pokemons with Held Items: %s', hunt_item_ball)
        logger.warning('[config.ini] Default ball for Shinies or Golden while Fishing: %s', fish_shiny_golden_ball)
        logger.warning("="*60 + "\n")      
        welcome_message = f"""
        {Fore.LIGHTMAGENTA_EX}
            
            ██████╗░░█████╗░██╗░░██╗███████╗███╗░░░███╗███████╗░█████╗░░██╗░░░░░░░██╗ 
            ██╔══██╗██╔══██╗██║░██╔╝██╔════╝████╗░████║██╔════╝██╔══██╗░██║░░██╗░░██║
            ██████╔╝██║░░██║█████═╝░█████╗░░██╔████╔██║█████╗░░██║░░██║░╚██╗████╗██╔╝
            ██╔═══╝░██║░░██║██╔═██╗░██╔══╝░░██║╚██╔╝██║██╔══╝░░██║░░██║░░████╔═████║░
            ██║░░░░░╚█████╔╝██║░╚██╗███████╗██║░╚═╝░██║███████╗╚█████╔╝░░╚██╔╝░╚██╔╝░
            ╚═╝░░░░░░╚════╝░╚═╝░░╚═╝╚══════╝╚═╝░░░░░╚═╝╚══════╝░╚════╝░░░░╚═╝░░░╚═╝░░
            
            ░█████╗░██╗░░░██╗████████╗░█████╗░██████╗░██╗░░░░░░█████╗░██╗░░░██╗
            ██╔══██╗██║░░░██║╚══██╔══╝██╔══██╗██╔══██╗██║░░░░░██╔══██╗╚██╗░██╔╝
            ███████║██║░░░██║░░░██║░░░██║░░██║██████╔╝██║░░░░░███████║░╚████╔╝░
            ██╔══██║██║░░░██║░░░██║░░░██║░░██║██╔═══╝░██║░░░░░██╔══██║░░╚██╔╝░░
            ██║░░██║╚██████╔╝░░░██║░░░╚█████╔╝██║░░░░░███████╗██║░░██║░░░██║░░░
            ╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░░╚════╝░╚═╝░░░░░╚══════╝╚═╝░░╚═╝░░░╚═╝░░░ {Style.RESET_ALL}  Version: {settings.version}

        """
        print(welcome_message)
        print("\n")