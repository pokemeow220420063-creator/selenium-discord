class Action:
    RETRY = 'retry'           # Thử lại (do cooldown, lag)
    SOLVE_CAPTCHA = 'solve_captcha' # Gặp captcha
    WAIT = 'wait'             # Chờ đợi
    CATCH_POKEMON = 'catch_pokemon' # Bắt (trạng thái bình thường)
    CATCH_AGAIN = 'catch_again' # Lỗi chưa bắt con cũ
    STOP_BOT = 'stop_bot'     # Dừng hẳn
    PAUSE = 'pause'           # Tạm dừng (hết lượt bắt)
    PROCEED = 'proceed'       # Tiếp tục
    UNKNOWN = 'unknown'       # Không rõ
    SKIP = 'skip'             # Bỏ qua (câu cá hụt)
    REFRESH = 'refresh'       # Mất kết nối (timeout)