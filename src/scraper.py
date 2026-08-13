import os
import re
from playwright.sync_api import sync_playwright
import time
from datetime import datetime


# =================================
# CẤU HÌNH
# =================================
MAX_IGNORED_ROWS = 8 # Số hàng bỏ qua (gồm các dòng thừa ở dưới)
THIS_YEAR = datetime.now().year


# =================================
# CODE
# =================================

def clear_console():
    """Làm cho console terminal đẹp hơn chút, tạo cảm giác mượt mà"""
    # 'nt' là Windows, 'posix' là Linux hoặc macOS
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)


class PTITScraper:
    def __init__(self, username: str, password: str, base_url: str):
        self.username = username
        self.password = password
        self.base_url = base_url

    def get_schedule(self):
        events = []
        with sync_playwright() as p:
            # Mở trình duyệt (để headless=False để bạn có thể nhìn thấy và nhập Captcha)
            browser = p.chromium.launch(headless=True) # headless=True để chạy ẩn
            context = browser.new_context()
            page = context.new_page()
            for i in range(0,3):
                print(f"--- Đang truy cập {self.base_url} ---")
                time.sleep(2)
                clear_console()
            # Truy cập trang web
            page.goto(self.base_url)

            # 1. Điền thông tin đăng nhập
            print("🪧  Điền thông tin đăng nhập...")
            page.fill('input[name="username"]', self.username)
            page.fill('input[name="password"]', self.password)
            page.keyboard.press("Enter")

            print("🔃 Tiến hành đăng nhập...")
            
            # Đợi mạng ổn định sau khi đăng nhập (không còn request nào sau 500ms)
            page.wait_for_load_state("networkidle", timeout=60000)
            print("✅ Đăng nhập thành công!")
            
            time.sleep(3) # Delay thêm một chút cho chắc chắn
            print("--- Đang chuyển hướng sang trang Lịch học theo tuần ---")
            time.sleep(2)
            clear_console()

            # 2. Điều hướng tới trang Lịch học theo tuần
            page.goto(f"{self.base_url}/public/#/tkb-tuan")
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # Đợi bảng lịch học xuất hiện (sửa lại selector hợp lệ: thay dấu cách bằng dấu chấm)
            page.wait_for_selector(".table.table-sm.user-select-none", timeout=30000)

            # 3. Logic lấy dữ liệu từ bảng (Scraping)
            rows = page.query_selector_all("tr")

            ## 3.1 Lấy danh sách ngày trong tuần từ hàng đầu tiên (bỏ cột đầu/cuối là mũi tên)
            header_cells = rows[0].query_selector_all("td")
            dates = [cell.inner_text().strip() for cell in header_cells[1:-1]]

            ## 3.2 Khử và lọc các dòng chứa dữ liệu tiết học thực sự (bỏ qua header/footer/điều hướng)
            data_rows = []
            for r in rows:
                tds = r.query_selector_all("td")
                if tds:
                    first_cell_text = tds[0].inner_text().strip()
                    if first_cell_text.startswith("Tiết"):
                        data_rows.append(r)

            num_rows = len(data_rows)
            num_cols = len(dates)
            virtual_grid = [[False for _ in range(num_cols)] for _ in range(num_rows)]

            events = []

            ## 3.3 Duyệt qua từng hàng dữ liệu tiết học
            for r_idx, row in enumerate(data_rows):
                tds = row.query_selector_all("td")

                # Bỏ td đầu tiên (tên tiết) và cột cuối cùng (Giờ)
                data_tds = tds[1:-1]
                td_pointer = 0

                # Xử lý rowspan
                for c_idx in range(num_cols):
                    # Nếu ô này đã bị chiếm bởi rowspan từ hàng trên -> bỏ qua cột này
                    if virtual_grid[r_idx][c_idx]:
                        continue

                    if td_pointer < len(data_tds):
                        td = data_tds[td_pointer]
                        content = td.inner_text().strip()
                        
                        # Kiểm tra rowspan
                        rowspan = int(td.get_attribute("rowspan") or 1)
                        if rowspan > 1:
                            for i in range(rowspan):
                                if r_idx + i < num_rows:
                                    virtual_grid[r_idx + i][c_idx] = True

                        # Nếu có nội dung môn học (không rỗng)
                        if content != "":
                            event = self._parse_cell_content(content, dates[c_idx])
                            if event:
                                events.append(event)

                        # Tăng con trỏ để sang ô tiếp theo
                        td_pointer += 1
            browser.close()
        return events


    def _parse_cell_content(self, text, date_header):
        """Tách thông tin từ nội dung ô và tiêu đề ngày"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) < 2:
            return None
            
        summary = lines[0] # Tên môn học
        
        # Lấy mã môn học nếu có ở dòng tiếp theo hoặc trong tiêu đề môn học
        course_code = ""
        match_code = re.search(r'\(([^)]+)\)$', summary)
        if match_code:
            course_code = match_code.group(1)
            summary = summary[:match_code.start()].strip()
        elif len(lines) > 1 and lines[1].startswith('(') and lines[1].endswith(')'):
            course_code = lines[1].strip('()')
            
        # Tìm động các thông tin khác trong các dòng
        group = ""
        location = ""
        teacher = ""
        start_time = "00:00"
        end_time = "00:00"
        
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if line_str.startswith("Nhóm:"):
                val = line_str.replace("Nhóm:", "").strip()
                if val:
                    group = val
                elif idx + 1 < len(lines):
                    group = lines[idx + 1].strip()
            elif line_str.startswith("Phòng:"):
                val = line_str.replace("Phòng:", "").strip()
                if val:
                    location = val
                elif idx + 1 < len(lines):
                    location = lines[idx + 1].strip()
            elif line_str.startswith("GV:"):
                val = line_str.replace("GV:", "").strip()
                if val:
                    teacher = val
                elif idx + 1 < len(lines):
                    teacher = lines[idx + 1].strip()
            elif line_str.startswith('->') or re.match(r'^->\s*\d{2}:\d{2}$', line_str):
                end_time = line_str.replace('->', '').strip()
            elif "->" in line_str:
                parts = [p.strip() for p in line_str.split("->")]
                if len(parts) == 2:
                    start_time = parts[0].strip()
                    end_time = parts[1].strip()
            elif re.match(r'^\d{2}:\d{2}$', line_str):
                start_time = line_str
                
        # Làm sạch thông tin phòng học
        if location:
            # Xử lý dạng trùng lặp như 505-A1-505-A1 (HN) thành 505-A1 (HN)
            parts = location.split(' ')
            room_part = parts[0]
            sub_parts = room_part.split('-')
            if len(sub_parts) == 4 and sub_parts[0] == sub_parts[2] and sub_parts[1] == sub_parts[3]:
                room_part = f"{sub_parts[0]}-{sub_parts[1]}"
                parts[0] = room_part
                location = ' '.join(parts)
            
            # Khử bớt các chữ thừa không cần thiết
            location = re.sub(r'\(HN\)|HN', '', location).strip()
            location = re.sub(r'\s+', ' ', location)
        
        # Trích xuất ngày từ header (Ví dụ: "Thứ 3 (10/03)" -> "10/03/2026")
        date_match = re.search(r'(\d{2}/\d{2})', date_header)
        date_str = f"{date_match.group(1)}/{THIS_YEAR}" if date_match else ""

        # Tạo phần mô tả sự kiện chi tiết
        desc_parts = []
        if course_code:
            desc_parts.append(f"Mã môn: {course_code}")
        if group:
            desc_parts.append(f"Nhóm: {group}")
        if teacher:
            desc_parts.append(f"GV: {teacher}")
        description = "\n".join(desc_parts)

        # Trả về summary chứa cả mã môn học để tương thích tốt với hiển thị trên Google Calendar
        event_summary = f"{summary} ({course_code})" if course_code else summary

        return {
            'summary': event_summary,
            'location': location,
            'description': description,
            'start': f"{date_str} {start_time}",
            'end': f"{date_str} {end_time}"
        }