import discord
from utils import Logger
from validators.action import Action

class ResponseValidator:
    @staticmethod
    def get_full_text(message: discord.Message) -> str:
        """Hàm trợ giúp: Gộp toàn bộ text trong tin nhắn (Content + Embed)"""
        text = (message.content or "") + " "
        
        if message.embeds:
            embed = message.embeds[0]
            text += (embed.title or "") + " "
            text += (embed.description or "") + " "
            if embed.footer:
                text += (embed.footer.text or "")
        
        return text.lower() # Chuyển về chữ thường để so sánh cho dễ

    @staticmethod
    def evaluate_response(message: discord.Message) -> str:
        """Phân tích tin nhắn để quyết định hành động tiếp theo"""
        
        # 1. Trường hợp không nhận được tin nhắn (Timeout)
        if message is None:
            Logger.error('No response from PokéMeow (Timeout). Retrying...')
            return Action.REFRESH
        
        # Lấy toàn bộ nội dung text
        full_text = ResponseValidator.get_full_text(message)

        # 2. KIỂM TRA CAPTCHA (Ưu tiên số 1)
        # Check cả keywords: captcha, human, verify
        if "captcha" in full_text or "verify" in full_text:
            Logger.error('🚨 A wild Captcha appeared! Action: SOLVE_CAPTCHA')
            return Action.SOLVE_CAPTCHA
        
        # 3. Các trường hợp Cooldown / Wait
        if "please wait" in full_text:
            Logger.log_transaction("System", "0", "Cooldown detected. Waiting...")
            return Action.RETRY
        
        if "you can now catch" in full_text:
            Logger.log_transaction("System", "0", "Cooldown finished. Retrying...")
            return Action.RETRY

        # 4. Lỗi Logic Game
        if "please catch the" in full_text:
            Logger.error('⚠️ Found uncaught Pokemon! Action: CATCH_AGAIN')
            return Action.CATCH_AGAIN

        # 5. Câu cá (Fishing)
        if "not even a nibble" in full_text:
            Logger.log_transaction("Fishing", "0", "🎣 Not even a nibble... Skipping.")
            return Action.SKIP

        # 6. Giới hạn ngày (Daily Limit)
        if "reached your daily catch" in full_text or "reached the daily" in full_text:
            Logger.error('⛔ Daily catch limit reached! Stopping bot.')
            return Action.PAUSE

        # 7. Nếu không dính lỗi nào -> Tiến hành bắt (PROCEED)
        return Action.PROCEED