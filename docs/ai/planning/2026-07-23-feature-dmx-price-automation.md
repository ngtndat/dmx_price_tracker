---
phase: planning
title: Implementation Task Plan
description: Kế hoạch triển khai mã nguồn từng bước cho tính năng dmx-price-automation.
---

# Implementation Task Plan: dmx-price-automation

## Task Breakdown

### Phase 1: Cấu hình Môi trường & Credentials
- [ ] **Task 1.1**: Tạo Telegram Bot qua `@BotFather`, lấy Telegram Bot Token & Chat ID nhóm.
- [ ] **Task 1.2**: Kiểm tra/Khởi tạo Google Sheets API Credential (`client_secret.json` hoặc Service Account JSON) và tạo file Google Sheets theo dõi.
- [ ] **Task 1.3**: Thiết lập danh sách sản phẩm mẫu theo dõi trong `products.json`.

### Phase 2: Phát triển Module Mã Nguồn (Python)
- [ ] **Task 2.1**: Viết module `dmx_scraper.py` sử dụng Playwright / BeautifulSoup4 bóc tách giá và tên sản phẩm ĐMX.
- [ ] **Task 2.2**: Viết module `gsheet_manager.py` kết nối Google Sheets API để append dữ liệu lịch sử giá.
- [ ] **Task 2.3**: Viết module `telegram_bot.py` gửi thông báo định dạng HTML/Markdown khi có sản phẩm giảm giá.
- [ ] **Task 2.4**: Viết script điều phối chính `main.py` tích hợp cả 3 module.

### Phase 3: Tự động hóa Lịch chạy & Kiểm thử (Verification)
- [ ] **Task 3.1**: Chạy kiểm thử E2E (`main.py`) xác nhận dữ liệu được ghi vào Google Sheets và tin nhắn gửi tới Telegram.
- [ ] **Task 3.2**: Thiết lập lịch tự động chạy 7:00 AM hàng ngày qua Windows Task Scheduler hoặc GitHub Actions.
