# Hướng Dẫn Quản Lý & Triển Khai DMX Price Tracker Qua Google Cloud Console CLI (`gcloud`)

Tài liệu này hướng dẫn chi tiết cách quản lý, cập nhật (update code), kích hoạt thủ công (trigger) và triển khai tự động ứng dụng **DMX Price Tracker** thông qua công cụ **Google Cloud Console CLI (`gcloud`)** hoặc **Google Cloud Shell**.

---

## 1. Yêu Cầu Tiền Đề (Prerequisites)

1. Cài đặt **Google Cloud SDK (`gcloud` CLI)** trên máy tính hoặc truy cập **[Google Cloud Shell](https://shell.cloud.google.com/)** trực tiếp trên trình duyệt.
2. Đã đăng nhập tài khoản GCP:
   ```bash
   gcloud auth login
   ```
3. Đặt dự án GCP mặc định (Project ID: `graphic-mission-503107-h2`):
   ```bash
   gcloud config set project graphic-mission-503107-h2
   ```

---

## 2. Phương Án Triển Khai 1: Cloud Run Jobs + Cloud Scheduler (Khuyên Dùng - 100% Serverless & Miễn Phí)

Mô hình này không cần duy trì máy chủ chạy 24/7. **Cloud Scheduler** sẽ kích hoạt **Cloud Run Job** đúng 08:00 AM hàng ngày để cào giá, đẩy Google Sheet, nhắn Telegram rồi tự động tắt.

### Bước 2.1: Bật các dịch vụ GCP API cần thiết qua CLI
```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    cloudscheduler.googleapis.com \
    sheets.googleapis.com
```

### Bước 2.2: Build Container Image & Deploy Job qua `gcloud`
Từ thư mục `day 2 - 20260721`:
```bash
# Build Docker image trên Google Cloud Build
gcloud builds submit --tag gcr.io/graphic-mission-503107-h2/dmx-price-tracker:latest .

# Tạo Cloud Run Job
gcloud run jobs create dmx-price-tracker-job \
    --image gcr.io/graphic-mission-503107-h2/dmx-price-tracker:latest \
    --region asia-east1 \
    --max-retries 1 \
    --set-env-vars SPREADSHEET_ID="1tcmSZmiOwbiOjpEi0jM_lxeEeTkUcITWJ6-jTvLri88",TELEGRAM_BOT_TOKEN="YOUR_TOKEN",TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
```

### Bước 2.3: Tạo Lịch Trình Tự Động 8h Sáng Mỗi Ngày Bằng Cloud Scheduler CLI
```bash
gcloud scheduler jobs create http dmx-daily-8am-trigger \
    --schedule="0 8 * * *" \
    --time-zone="Asia/Ho_Chi_Minh" \
    --uri="https://asia-east1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/graphic-mission-503107-h2/jobs/dmx-price-tracker-job:run" \
    --http-method=POST \
    --oauth-service-account-email="test-120@graphic-mission-503107-h2.iam.gserviceaccount.com"
```

---

## 3. Các Câu Lệnh CLI Để Cập Nhật & Quản Lý Từ Google Cloud Console CLI

### 🔄 A. Cập Nhật Code (Update Application Code)
Mỗi khi bạn sửa code scraper hoặc thay đổi thông số, chỉ cần chạy 2 lệnh CLI sau để cập nhật phiên bản mới nhất lên GCP:
```bash
# 1. Re-build image với code mới
gcloud builds submit --tag gcr.io/graphic-mission-503107-h2/dmx-price-tracker:latest .

# 2. Update Cloud Run Job
gcloud run jobs update dmx-price-tracker-job \
    --image gcr.io/graphic-mission-503107-h2/dmx-price-tracker:latest \
    --region asia-east1
```

### ⚡ B. Chạy Thủ Công Tức Thì (Execute / Trigger Now)
Để test quy trình ngay lập tức từ CLI mà không cần chờ 8:00 AM:
```bash
gcloud run jobs execute dmx-price-tracker-job --region asia-east1
```

### 📋 C. Xem Nhật Ký / Log Hệ Thống (View Execution Logs)
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=dmx-price-tracker-job" \
    --limit 30 \
    --format="table(timestamp, textPayload)"
```

### ⚙️ D. Cập Nhật Môi Trường / Biến Cấu Hình (Update Env Vars)
Ví dụ cập nhật Telegram Token mới hoặc Sheet ID mới từ CLI:
```bash
gcloud run jobs update dmx-price-tracker-job \
    --region asia-east1 \
    --update-env-vars TELEGRAM_BOT_TOKEN="YOUR_NEW_TOKEN",TELEGRAM_CHAT_ID="YOUR_NEW_CHAT_ID"
```

---

## 4. Phương Án Triển Khai 2: Compute Engine VM (`gcloud compute`)

Nếu bạn muốn chạy ứng dụng trên 1 máy chủ ảo Compute Engine riêng biệt:

### 4.1: Tạo VM bằng `gcloud`
```bash
gcloud compute instances create dmx-tracker-vm \
    --zone=asia-east1-a \
    --machine-type=e2-micro \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --service-account=test-120@graphic-mission-503107-h2.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/cloud-platform
```

### 4.2: SSH & Cập Nhật Code Trên VM Qua CLI
```bash
# SSH vào máy chủ ảo từ Cloud Console CLI
gcloud compute ssh dmx-tracker-vm --zone=asia-east1-a

# Chạy cập nhật code trên VM
cd ~/day\ 2\ -\ 20260721/
git pull
python3 main_automation.py --now
```

---
*Tài liệu thuộc ai-devkit project `day 2 - 20260721`*
