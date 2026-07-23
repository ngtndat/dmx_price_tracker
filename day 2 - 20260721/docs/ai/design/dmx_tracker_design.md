# AI-Devkit Architecture & Design: Điện Máy Xanh Price Tracker

## 1. Sơ Đồ Kiến Trúc Hệ Thống (System Architecture)

```
+---------------------------------------------------------------+
|                      Dien May Xanh (DMX)                      |
|                  https://www.dienmayxanh.com                  |
+-------------------------------+-------------------------------+
                                | (HTTP GET / BeautifulSoup4)
                                v
+---------------------------------------------------------------+
|                     dmx_scraper.py                            |
|  - Parse product list & detail pages                          |
|  - Clean price, promotions & availability status             |
+-------------------------------+-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
|                     main_automation.py                        |
|  - Process scraped data                                       |
|  - Compare current price with stored state / threshold        |
+-----------------------+---------------+-----------------------+
                        |               |
                        v               v
+-------------------------------+ +-----------------------------+
|       sheets_updater.py       | |    telegram_notifier.py     |
| (Service Account Auth)        | | (Telegram Bot API)          |
| -> Google Sheets Dashboard    | | -> Discount Alerts Msg      |
+-------------------------------+ +-----------------------------+
```

## 2. Các Module Chính

| File Script | Vai trò / Chức năng |
|---|---|
| `config.py` | Nơi tập trung cấu hình: API keys, Google Sheet ID, URL sản phẩm DMX mục tiêu, ngưỡng cảnh báo. |
| `dmx_scraper.py` | Bóc tách HTML Điện Máy Xanh thành dữ liệu JSON chuẩn hóa. |
| `sheets_updater.py` | Tương tác Google Sheets API (gspread / google-api-python-client) để ghi báo cáo. |
| `telegram_notifier.py` | Gửi thông báo Telegram HTML khi phát hiện đối thủ giảm giá. |
| `main_automation.py` | Điều phối quy trình cào -> so sánh -> ghi Sheet -> phát cảnh báo Telegram. |
| `scheduler.py` | Lập lịch chạy 8:00 AM mỗi ngày bằng `APScheduler`. |
| `gcloud_deploy.sh` | Script quản lý & deploy tự động qua Google Cloud Console CLI (`gcloud`). |

---
*Tài liệu thuộc ai-devkit project `day 2 - 20260721`*
