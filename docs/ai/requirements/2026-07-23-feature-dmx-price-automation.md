---
phase: requirements
title: Automation Quét Giá Điện Máy Xanh & Cảnh Báo Telegram / Google Sheets
description: Quy trình dán link sản phẩm, quét giá test xuất Google Sheet, hẹn giờ 2 tiếng và bật Telegram sau khi duyệt.
---

# Requirements & Problem Understanding: dmx-price-automation

## Problem Statement
Chuyên viên kinh doanh cần dán đường link sản phẩm Điện Máy Xanh, tiến hành kiểm tra (Test) xem thông tin **Giá bán, Giá gốc, % Giảm giá** có chính xác 100% khi xuất sang Google Sheets hay chưa, trước khi kích hoạt tính năng tự động phát thông báo tới Telegram.

## Workflow & Requirements

1. **Dán đường link sản phẩm**:
   - Cho phép người dùng nhập trực tiếp 1 hoặc nhiều link URL sản phẩm ĐMX vào tệp cấu hình hoặc giao diện điều khiển.
   - Tích hợp bộ cào dữ liệu nâng cao từ Google Colab scraper (xử lý cả `bs_price`, `box-price-present`, `box-price-old`, và `JSON-LD Schema`).

2. **Kiểm thử (Test) & Xuất dữ liệu sang Google Sheets**:
   - Chạy quét tức thì và in bảng tổng hợp chi tiết ra màn hình Console (Tên SP, Giá bán, Giá gốc, % Giảm, Trạng thái).
   - Xuất dữ liệu tự động sang Google Sheets để người dùng soi xét và đối chiếu trực quan.

3. **Chỉ bật Telegram khi Test ổn định**:
   - Tính năng gửi tin nhắn Telegram mặc định ở trạng thái **TẮT (OFF)**.
   - Khi người dùng kiểm tra dữ liệu trên Google Sheets thấy chuẩn xác, có thể bấm công tắc để chuyển sang **BẬT (ON)**.

4. **Hẹn giờ quét định kỳ 2 tiếng (Chạy nền in-app hoặc Server)**:
   - Tự động thực hiện lại chu trình quét sau mỗi 2 tiếng kể từ lúc dán link.
