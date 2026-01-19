import asyncio
import re
from logger import Logger

logger = Logger().get_logger()

class Quest:
    @staticmethod
    async def actions(driver, inventory):
        """
        Refactor: Chuyển sang Async, dùng driver API.
        """
        # 1. Gửi lệnh kiểm tra Quest
        logger.info("[Quest] Checking quests...")
        await driver.write(";q")
        
        # 2. Đợi phản hồi
        quests_message = await driver.get_last_element_by_user("PokéMeow")
        
        if not quests_message:
            logger.info("[Quest] No response from bot.")
            return

        content = quests_message.content or ""

        # 3. Check "Please wait"
        if "please wait" in content.lower():
            await asyncio.sleep(4.5)
            logger.info("[Quest] Please wait...")
            await Quest.actions(driver, inventory) # Đệ quy
            return

        # 4. Parse danh sách Quest
        quests_list = Quest.get_quests_list(quests_message)
        
        # 5. Kiểm tra vé Quest Reset
        reroll_count = next((item['count'] for item in inventory if item['name'] == 'questreset'), 0)
        
        await asyncio.sleep(2)
        
        # 6. Logic Reroll
        if reroll_count and reroll_count > 0:
            for _ in range(reroll_count):
                # Duyệt qua từng quest đang có
                for quest in quests_list:
                    for key, value in quest.items():
                        # Nếu quest KHÔNG PHẢI "dexcaught" -> Reroll
                        if value != "dexcaught":
                            logger.info(f"[Quest] Rerolling quest {key} ({value})...")
                            
                            new_message = await Quest.reroll_quest(driver, key)
                            await asyncio.sleep(4)
                            
                            if new_message is None:
                                break
                            
                            # Cập nhật lại list quest
                            quests_list = Quest.get_quests_list(new_message)
                            break # Break inner loop để check lại từ đầu

    @staticmethod
    def get_quests_list(message):
        """
        Parse Embed để lấy danh sách Quest
        Output: List [{1: 'dexcaught'}, {2: 'battle'}]
        """
        quest_data = []
        if not message.embeds:
            return quest_data

        description = message.embeds[0].description or ""
        
        for line in description.split('\n'):
            # Tìm số thứ tự Quest
            num_match = re.search(r'\*\*Quest #(\d+)\*\*:', line)
            if not num_match:
                num_match = re.search(r'\*\*(\d+)\.\*\*', line)

            if num_match:
                quest_number = int(num_match.group(1))
                emoji_name = "unknown"

                # Tìm Emoji biểu thị loại Quest
                custom_emoji = re.search(r'<:(\w+):', line)
                simple_emoji = re.search(r':(\w+):', line)

                if custom_emoji:
                    emoji_name = custom_emoji.group(1)
                elif simple_emoji:
                    if simple_emoji.group(1).lower() != "quest":
                        emoji_name = simple_emoji.group(1)
                
                quest_data.append({quest_number: emoji_name})

        return quest_data

    @staticmethod
    async def reroll_quest(driver, quest_number: int):
        await driver.write(f";q r {quest_number}")
        
        quests_message = await driver.get_last_element_by_user("PokéMeow")
        
        if not quests_message:
            return None
            
        content = (quests_message.content or "").lower()
        
        if "please wait" in content:
            await asyncio.sleep(3.5)
            logger.info("[Quest Reroll] Please wait...")
            return await Quest.reroll_quest(driver, quest_number)
        
        if "don't have any quest reset" in content:
            logger.info("[Quest Reroll] You don't have any quest reset...")
            return None

        return quests_message