---
phase: testing
title: Test Plan & Scenarios
description: Kế hoạch thử nghiệm và các kịch bản kiểm thử cho hệ thống dmx-price-automation.
---

# Test Plan & Scenarios: dmx-price-automation

## Unit Test Scenarios

- [ ] **Scraper Test**: Kiểm tra `dmx_scraper.py` bóc tách thành công giá sản phẩm mẫu từ ĐMX.
- [ ] **GSheets Test**: Kiểm tra `gsheet_manager.py` kết nối thành công Google Sheets và ghi dòng mới.
- [ ] **Telegram Bot Test**: Kiểm tra `telegram_bot.py` gửi tin nhắn test thành công tới Telegram Chat ID.
- [ ] **Price Change Calculation Test**: Kiểm tra logic so sánh giá cũ vs giá mới để phát hiện chính xác trường hợp giảm giá.

## Integration & Edge Cases

- [ ] **Edge Case 1 - Sản phẩm hết hàng**: Scraper ghi nhận đúng trạng thái "Out of Stock" và không báo lỗi crash.
- [ ] **Edge Case 2 - Website ĐMX đổi giao diện/anti-bot**: Playwright/Scraper catch exception và ghi log rõ ràng.
- [ ] **Edge Case 3 - Google API Token Hết hạn**: Cấu hình refresh token / service account tự động cấp lại quyền.

## E2E Dry-Run Validation

- [ ] Chạy `python main.py --dry-run` thành công toàn bộ chu trình từ cào dữ liệu ➔ ghi Sheets ➔ phát thông báo Telegram.
