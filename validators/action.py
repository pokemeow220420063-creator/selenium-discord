class Action:
    RETRY = 'retry'
    SOLVE_CAPTCHA = 'solve_captcha'
    CATCH_AGAIN = 'catch_again'
    PAUSE = 'pause'
    PROCEED = 'proceed'
    SKIP = 'skip'
    REFRESH = 'refresh' # Vẫn giữ để Validator trả về đúng y hệt code cũ (không dùng nữa vì API không dùng)

    # Các action cũ không dùng, giữ lại cho đủ bộ nếu muốn
    UNKNOWN = 'unknown'
    WAIT = 'wait'
    CATCH_POKEMON = 'catch_pokemon'
    STOP_BOT = 'stop_bot'