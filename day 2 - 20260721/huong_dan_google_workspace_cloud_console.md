# Hướng Dẫn Tạo Và Liên Kết Google Workspace Thông Qua Google Cloud Console

Tài liệu này hướng dẫn chi tiết từng bước để tạo dự án (Project), thiết lập liên kết tổ chức (Organization), bật các API và cấu hình ủy quyền truy cập giữa **Google Workspace** (hoặc tài khoản Google cá nhân) và **Google Cloud Console (GCP)**.

---

## 1. Phân Biệt Tài Khoản Google Workspace vs Gmail Cá Nhân

> [!IMPORTANT]
> **Điểm khác biệt quan trọng:**
> - **Google Workspace (`@domain_cong_ty.com`)**: Có quyền truy cập trang Quản trị `admin.google.com`, thiết lập Organization và ủy quyền toàn miền (Domain-Wide Delegation).
> - **Gmail Cá Nhân (`@gmail.com`)**: **KHÔNG THỂ** đăng nhập vào `admin.google.com`. Bạn chỉ cần tạo OAuth 2.0 Client ID ở Cloud Console và xác thực thông qua trình duyệt khi chạy ứng dụng.

---

## 2. Các Bước Thực Hiện Chi Tiết

### Bước 1: Đăng Nhập GCP Console Và Tạo Dự Án (Project)
1. Truy cập vào **[Google Cloud Console](https://console.cloud.google.com/)**.
2. Trên thanh điều hướng trên cùng, chọn menu Dự án (Project Selector) > Nhấn **New Project**.
3. Nhập tên dự án (ví dụ: `My-Workspace-App`) và nhấn **Create**.

---

### Bước 2: Kích Hoạt Các API Cần Thiết
1. Vào menu bên trái > **APIs & Services** > **Library**.
2. Tìm và bật (**Enable**) các API bạn cần dùng:
   - **Gmail API** (Đọc/Gửi mail)
   - **Google Drive API** (Quản lý tệp)
   - **Google Sheets API** (Thao tác trang tính)
   - **Admin SDK API** *(Chỉ dùng nếu có Google Workspace)*

---

### Bước 3: Cấu Hình Màn Hình Chấp Thuận OAuth (Google Auth Platform > Branding)
1. Vào **Google Auth Platform** > **Branding**:
   - **App name**: Nhập tên ứng dụng (ví dụ: `Automation App`).
   - **User support email**: Chọn email của bạn.
   - Nhấn **Next**.
2. **Audience**:
   - Chọn **Internal** nếu dùng Workspace công ty.
   - Chọn **External** nếu dùng Gmail cá nhân (Cần thêm email vào mục **Audience** > **Test Users**).
3. **Contact Information**: Nhập email liên hệ nhà phát triển > Nhấn **Next** > Nhấn **Create**.

---

### Bước 4: Tạo Và Lấy OAuth 2.0 Client ID (Cho cả Gmail cá nhân & Workspace)
1. Vào menu trái **Google Auth Platform** > **Clients**.
2. Nhấn **+ Create Client**.
3. Select **Application type**:
   - Chọn **Desktop app** (nếu chạy script Python / Node.js trên máy).
   - Chọn **Web application** (nếu làm trang web).
4. Nhập tên Client > Nhấn **CREATE**.
5. Tải tệp cấu hình chứa **Client ID** & **Client Secret** (Bấm **DOWNLOAD JSON**).

---

### Bước 5: Ủy Quyền Xử Lý (Phân nhánh theo loại tài khoản)

#### ✅ NẾU DÙNG GMAIL CÁ NHÂN (`@gmail.com`):
- **BẠN BỎ QUA TRANG `admin.google.com`**.
- Bạn chỉ cần dùng file `.json` vừa tải ở Bước 4. Khi ứng dụng Python chạy lần đầu, nó sẽ mở trình duyệt yêu cầu bạn nhấn **Allow (Cho phép)** để cấp quyền truy cập.

#### 🏢 NẾU DÙNG GOOGLE WORKSPACE DOANH NGHIỆP (`@congty.com`):
1. Đăng nhập trang Quản trị: **[admin.google.com](https://admin.google.com/)** bằng tài khoản **Super Admin** của công ty (không dùng `@gmail.com`).
2. Vào **Security** > **Access and data control** > **API controls** > **Domain-wide delegation**.
3. Nhấn **Add new**, nhập **Client ID** của Service Account / OAuth Client và các Scopes cần cấp.
4. Nhấn **Authorize**.

---
*Tài liệu được lưu trữ tại thư mục: `day 2 - 20260721/huong_dan_google_workspace_cloud_console.md`*
