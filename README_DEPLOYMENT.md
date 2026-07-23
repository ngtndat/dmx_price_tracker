# Hướng Dẫn Triển Khai Web App & Xuất Bản Lên YouTube

Tài liệu hướng dẫn triển khai ứng dụng **YouTube Chinese Story Dubber & Translator** lên máy chủ (VPS/Cloud) trỏ domain chính thức và quy trình xuất bản video lên YouTube.

---

## 🚀 1. Chạy Ứng Dụng Trên Máy Cụm Local (Development)

### Bước 1: Khởi động Backend Python FastAPI
```bash
cd d:\Antigravity
python -m venv venv
venv\Scripts\activate
pip install -r youtube_dubber_backend/requirements.txt
uvicorn youtube_dubber_backend.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- WebSocket Progress: `ws://localhost:8000/ws/dub/progress/{job_id}`

### Bước 2: Mở Giao diện Web Frontend
- Mở trực tiếp file [index.html](file:///d:/Antigravity/youtube_dubber_frontend/index.html) trong trình duyệt web, hoặc mở thông qua bất kỳ HTTP static server nào (`http-server`, Live Server trong VSCode).

---

## 🌐 2. Triển Khai Lên Server Production & Trỏ Domain Chính (Custom Domain)

Hệ thống đã chuẩn bị sẵn `docker-compose.yml` để bạn triển khai chỉ bằng 1 dòng lệnh lên máy chủ VPS (Ubuntu/Debian/CentOS):

### Bước 1: Clone Code & Chạy Docker
```bash
git clone <your-repo-url> /opt/youtube-dubber
cd /opt/youtube-dubber
docker-compose up -d --build
```

### Bước 2: Đăng ký SSL Certbot & Nginx Reverse Proxy (Domain Chính)
Để kết nối SSL `https://your-domain.com` và `wss://your-domain.com`:

```nginx
server {
    server_name your-domain.com;

    location / {
        root /usr/share/nginx/html;
        index index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```

```bash
sudo certbot --nginx -d your-domain.com
```

---

## 🎬 3. Mẹo Tối Ưu Đăng Video Lên YouTube (Chống Bản Quyền 100%)

1. **Bật Chế độ "Biến đổi Video lách Bản quyền (Anti-Copyright)" trên Web App**:
   - Hệ thống tự động áp dụng: Lật ngang hình ảnh (`hflip`), tăng tốc độ 1.03x nhẹ, crop viền 4%, điều chỉnh dải màu và trộn nhạc nền chìm.
2. **Tiêu đề & Mô tả YouTube**:
   - Đặt tiêu đề thu hút bằng Tiếng Việt hoặc Tiếng Anh (Ví dụ: *"[Truyện Ngắn Audio] Bí Mật Của Cụ Già Trong Rừng Sâu | Thuyết Minh Tiếng Việt HD"*).
3. **Phụ đề (.SRT)**:
   - Tải file `.srt` từ web app về và upload vào phần **Subtitles / Phụ đề** trong YouTube Studio để tăng điểm SEO tìm kiếm.
