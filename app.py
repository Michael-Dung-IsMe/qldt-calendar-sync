import os
from dotenv import load_dotenv
from src.scraper import PTITScraper
from src.calendar_api import GoogleCalendarManager
import pandas as pd
import json

load_dotenv()

def main():
    # 1. Lấy cấu hình từ .env
    user = os.getenv("PTIT_USERNAME")
    pw = os.getenv("PTIT_PASSWORD")
    web = os.getenv("TARGET_URL")
    
    # 2. Chạy Scraper để lấy lịch từ web
    scraper = PTITScraper(user, pw, web)
    print("🚀 Đang bắt đầu quá trình lấy lịch...")
    schedule_data = scraper.get_schedule()
    
    if not schedule_data:
        print("📭 Không tìm thấy dữ liệu lịch học mới.")
        return
    
    # 2.1 Lưu dữ liệu cào lịch về json trên local
    # with open("temp.json", 'w', encoding="utf-8") as tmp:
    #     json.dump(schedule_data, tmp, ensure_ascii=False, indent=4)

    # 3. Đẩy lên Google Calendar
    calendar = GoogleCalendarManager()
    calendar.sync_events(schedule_data)
    
    print("\n✨ Tuyệt vời! Lịch của bạn đã được cập nhật.")
    print("Vào Google Calendar để kiểm tra thành quả nhé!")

    # Nếu muốn lấy lịch về file csv thì bỏ comment đoạn code này
    # df = pd.DataFrame(schedule_data)
    # df.to_csv("schedule.csv", index=False, encoding='utf-8-sig')

    # Test thử data trên local
    # import re
    # with open('temp.json', 'r', encoding='utf-8') as f:
    #     lines = json.load(f)
    #     for line in lines:
    #         # Loại bỏ nội dung dư thừa
    #         pattern = r"\bPhòng: \b|HN|\(Cơ sở Ngọc Trục\)|Cơ sở Ngọc Trục"
    #         res = re.sub(pattern, "", line['location']).replace("  ", " ").replace("()", "").strip()
    #         x = round(len(res)/2)
    #         if 'LMS' in res:
    #             x = len(res)
    #         elif 'học' in res:
    #             x = 10
    #         line['location'] = res[:x]
    #         print(line)

if __name__ == "__main__":
    main()