import os
from bs4 import BeautifulSoup
import time

# ĐÃ SỬA TÊN HÀM THÀNH dump_html CHO KHỚP VỚI LỆNH GỌI
def dump_html(element, filename="debug_dump.html"):
    """
    Lưu toàn bộ HTML của element ra file để soi.
    """
    try:
        # 1. Tạo thư mục debug nếu chưa có
        if not os.path.exists("debug_html"):
            os.makedirs("debug_html")

        # 2. Lấy HTML thô từ Selenium
        # Kiểm tra xem có phải element thật không hay là chuỗi text
        if hasattr(element, 'get_attribute'):
            raw_html = element.get_attribute('outerHTML')
        else:
            raw_html = str(element)

        # 3. Làm đẹp code (Format cho dễ nhìn)
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            pretty_html = soup.prettify()
        except Exception:
            # Nếu lỗi format (do thiếu thư viện hoặc lỗi html) thì dùng raw luôn
            pretty_html = raw_html

        # 4. Xử lý tên file để không bị lỗi đường dẫn
        # Lấy tên file gốc, bỏ các ký tự thừa
        clean_name = os.path.basename(filename) 
        timestamp = int(time.time())
        
        # Lưu vào thư mục debug_html với timestamp để không bị ghi đè
        # Ví dụ: debug_html/170548123_catchbot_response.html
        final_path = f"debug_html/{timestamp}_{clean_name}"
        
        # Đảm bảo có đuôi .html
        if not final_path.endswith(".html"):
            final_path += ".html"

        with open(final_path, "w", encoding="utf-8") as f:
            f.write(pretty_html)
            
        print(f"📸 Đã lưu HTML vào file: {final_path}")
        return pretty_html

    except Exception as e:
        print(f"⚠️ Lỗi lưu HTML: {e}")
        return ""