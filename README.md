# 📅 QLDT Calendar Sync

> Tự động lấy lịch học từ [QLDT PTIT](https://qldt.ptit.edu.vn/) và đồng bộ lên **Google Calendar** — giúp sinh viên PTIT quản lý thời gian học tập dễ dàng hơn.

---

## 📖 Giới thiệu

**QLDT Calendar Sync** là một công cụ tự động hóa giúp sinh viên Học viện Công nghệ Bưu chính Viễn thông (PTIT) đồng bộ lịch học từ hệ thống Quản lý Đào tạo (QLDT) lên Google Calendar.

### Tại sao cần công cụ này?

- Hệ thống QLDT không hỗ trợ xuất lịch trực tiếp sang các ứng dụng lịch phổ biến.
- Sinh viên phải vào web QLDT mỗi lần muốn kiểm tra lịch học — rất bất tiện.
- Với công cụ này, lịch học sẽ được tự động đẩy lên Google Calendar (hoặc Notion Calendar), giúp bạn xem lịch mọi lúc mọi nơi trên điện thoại, máy tính.

### Công cụ hoạt động như thế nào?

1. **Scraping** — Sử dụng [Playwright](https://playwright.dev/) để mở trình duyệt, tự động đăng nhập vào QLDT và lấy dữ liệu lịch học theo tuần từ bảng thời khóa biểu.
2. **Parsing** — Phân tích dữ liệu thô từ bảng HTML (xử lý `rowspan`, trích xuất tên môn, phòng học, giảng viên, giờ học).
3. **Syncing** — Kết nối với Google Calendar API, kiểm tra trùng lặp và chỉ thêm các sự kiện mới lên lịch.

---

## 📁 Cấu trúc dự án

```
qldt-calendar-sync/
├── app.py                  # Entry point — Điểm khởi chạy chương trình
├── src/
│   ├── scraper.py          # Module scraping — Lấy lịch từ QLDT bằng Playwright
│   └── calendar_api.py     # Module Google Calendar — Xác thực & đồng bộ sự kiện
├── credentials.json        # OAuth 2.0 credentials (Google Cloud Console)
├── token.json              # Token xác thực Google (tự sinh sau lần đăng nhập đầu)
├── requirements.txt        # Danh sách thư viện Python cần thiết
├── .env                    # Biến môi trường (tài khoản QLDT, URL)
└── .env.example            # Mẫu file .env
```

### Mô tả chi tiết

| File / Thư mục        | Mô tả                                                                                                                      |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `app.py`              | File chính, điều phối luồng: đọc cấu hình → scrape lịch → đồng bộ lên Calendar                                             |
| `src/scraper.py`      | Class `PTITScraper` — tự động đăng nhập QLDT, điều hướng đến trang _Lịch học theo tuần_, và parse bảng thời khóa biểu      |
| `src/calendar_api.py` | Class `GoogleCalendarManager` — xác thực OAuth 2.0 với Google, kiểm tra trùng lặp, và tạo sự kiện mới trên Google Calendar |
| `credentials.json`    | File chứa Client ID & Client Secret từ Google Cloud Console (không được đẩy lên Git)                                       |
| `token.json`          | File lưu access/refresh token, được tạo tự động sau lần xác thực đầu tiên                                                  |
| `.env`                | Chứa thông tin đăng nhập QLDT và URL mục tiêu                                                                              |

---

## 🚀 Hướng dẫn cài đặt

### Yêu cầu hệ thống

- **Python** 3.10+
- **Google Account** (để sử dụng Google Calendar API)
- Tài khoản **QLDT PTIT**

### Bước 1: Clone dự án

```bash
git clone https://github.com/<your-username>/qldt-calendar-sync.git
cd qldt-calendar-sync
```

### Bước 2: Tạo môi trường ảo & cài đặt thư viện

Khuyến khích sử dụng **virtual environment** để tránh xung đột thư viện. Chọn **một trong hai** cách sau:

#### Cách 1: Sử dụng `venv`

```bash
python -m venv venv
venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
```

#### Cách 2: Sử dụng `conda`

```bash
conda create -n qldt-sync python=3.10 -y
conda activate qldt-sync
pip install -r requirements.txt
```

### Bước 3: Cài đặt trình duyệt cho Playwright

```bash
playwright install chromium
```

### Bước 4: Thiết lập Google Calendar API

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/).
2. Tạo một **Project** mới (hoặc chọn project đã có).
3. Bật **Google Calendar API** tại mục _APIs & Services > Library_.
4. Tạo **OAuth 2.0 Client ID** tại mục _APIs & Services > Credentials_:
   - Application type: **Desktop app**
   - Tải file JSON về và đổi tên thành `credentials.json`.
5. Đặt file `credentials.json` vào **thư mục json** của dự án.

### Bước 5: Cấu hình biến môi trường

Tạo file `.env` từ file mẫu:

```bash
cp .env.example .env
```

Chỉnh sửa file `.env` với thông tin của bạn:

```env
PTIT_USERNAME="MSV"
PTIT_PASSWORD="Mật khẩu QLDT"
TARGET_URL="https://qldt.ptit.edu.vn/"
```

### Bước 6: Chạy chương trình

```bash
python app.py
```

> **Lưu ý:** Lần chạy đầu tiên, trình duyệt sẽ mở để bạn xác thực tài khoản Google. Token sẽ được lưu tự động vào `token.json` cho các lần sau.

---

## ⚙️ Lưu ý thêm

- Chương trình mặc định chạy ở chế độ **có giao diện** (`headless=False`) để bạn có thể quan sát quá trình scraping. Nếu muốn chạy ẩn, thay đổi trong `src/scraper.py`:
  ```python
  browser = p.chromium.launch(headless=True)
  ```
- Sự kiện được đồng bộ sẽ kèm nhắc nhở **trước 30 phút**.
- Chương trình tự động kiểm tra **trùng lặp** — chạy lại nhiều lần sẽ không tạo sự kiện bị trùng.
- Nếu muốn xuất lịch ra file CSV, bỏ comment đoạn code cuối trong `app.py`.

---

<p align="center">
  Made with ❤️ by Michael-Dung
</p>
