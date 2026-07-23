# AI-Devkit Specification: Điện Máy Xanh Price Tracker Requirements

## 1. Mục Tiêu (Objective)
Tự động hóa hoàn toàn quy trình quét giá sản phẩm (đối thủ & sản phẩm chính) trên hệ thống Điện Máy Xanh (DMX) hàng ngày lúc 08:00 AM, cập nhật báo cáo trực quan lên Google Sheets và gửi thông báo khẩn cấp qua Telegram Bot khi có sản phẩm biến động giá / giảm giá mạnh.

## 2. Phạm Vi & Tính Năng Chi Tiết (Scope & Features)

### 2.1. Web Scraping Điện Máy Xanh
- Quét danh mục sản phẩm (Tivi, Máy lạnh, Tủ lạnh, Máy giặt, Gia dụng...) hoặc theo các URL chỉ định.
- Bóc tách thông tin chi tiết:
  - Tên sản phẩm & Mã Model
  - Giá niêm yết (MRP Price)
  - Giá bán ưu đãi (Selling Price)
  - Mức giảm giá (Số tiền giảm & % giảm)
  - Thông tin quà tặng / khuyến mãi đi kèm
  - Trạng thái sản phẩm (Đang kinh doanh / Mẫu mới / Ngừng kinh doanh)
  - Link trực tiếp đến trang sản phẩm.

### 2.2. Cập Nhật Google Sheets
- Sử dụng Service Account authentication (`graphic-mission-503107-h2-cc040963a75b.json`).
- Tab 1: `Báo Cáo Giá DMX Hàng Ngày` - Tổng hợp bảng giá mới nhất lúc 8h sáng.
- Tab 2: `Lịch Sử Giảm Giá` - Ghi log chi tiết các đợt giảm giá theo thời gian.

### 2.3. Cảnh Báo Telegram Bot
- Gửi tin nhắn định dạng HTML sinh động tới Telegram Chat ID / Channel.
- Điều kiện kích hoạt: Sản phẩm đối thủ/chính có giá bán giảm so với lần quét trước hoặc có mức giảm giá >= 5% so với giá niêm yết.
- Bao gồm link bấm nhanh tới sản phẩm DMX và chi tiết mức giảm.

### 2.4. Google Cloud Console CLI (`gcloud`) Integration
- Hỗ trợ triển khai serverless trên **GCP Cloud Run / Cloud Functions** hoặc **Compute Engine VM**.
- Cung cấp kịch bản CLI (`gcloud`) cho phép quản lý, kích hoạt (trigger), kiểm tra log và update code từ xa bằng terminal CLI.

---
*Tài liệu thuộc ai-devkit project `day 2 - 20260721`*
