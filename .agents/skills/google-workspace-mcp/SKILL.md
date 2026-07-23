---
name: google-workspace-mcp
description: >
  Tương tác và quản lý Google Workspace (Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Tasks, Contacts, Chat, Apps Script, Custom Search)
  thông qua MCP server hoặc CLI tool workspace-mcp.
  Sử dụng khi người dùng yêu cầu đọc/gửi email Gmail, quản lý file/thư mục Google Drive, đặt lịch Google Calendar, thao tác Google Sheets/Docs, hoặc tạo công việc Google Tasks.
---

# Google Workspace MCP Skill

Skill này cung cấp khả năng điều khiển toàn bộ hệ sinh thái Google Workspace bằng ngôn ngữ tự nhiên thông qua gói `google-workspace-mcp` cài đặt tại `d:\Antigravity\google-workspace-mcp`.

## 1. Cấu hình Credentials

Dự án đã được liên kết với Google OAuth Client ID & Secret:
- **Client ID**: `YOUR_CLIENT_ID.apps.googleusercontent.com`
- **Client Secret**: `YOUR_CLIENT_SECRET`
- **File Secret JSON**: `d:\Antigravity\google-workspace-mcp\credentials\client_secret.json`
- **File Môi Trường**: `d:\Antigravity\google-workspace-mcp\.env`

## 2. Cách Thực Thi (Execution Modes)

### Cách 1: Sử dụng MCP Server (Khuyên dùng)
Chạy MCP server với `uv`:
```powershell
uv run --directory d:\Antigravity\google-workspace-mcp workspace-mcp --tool-tier complete
```

### Cách 2: Sử dụng CLI
Gọi trực tiếp các công cụ Google Workspace từ dòng lệnh PowerShell:
```powershell
uv run --directory d:\Antigravity\google-workspace-mcp workspace-mcp --cli <tool_name> --args '{"user_google_email": "YOUR_EMAIL", ...}'
```

Ví dụ kiểm tra Gmail:
```powershell
uv run --directory d:\Antigravity\google-workspace-mcp workspace-mcp --cli list_gmail_messages --args '{"user_google_email": "me", "max_results": 5}'
```

Ví dụ liệt kê tệp Google Drive:
```powershell
uv run --directory d:\Antigravity\google-workspace-mcp workspace-mcp --cli list_drive_files --args '{"page_size": 10}'
```

## 3. Các Dịch Vụ Hỗ Trợ (12 Services)

1. **Gmail**: Đọc, gửi, gắn nhãn, tìm kiếm email.
2. **Google Drive**: Tìm kiếm, tải lên, tạo thư mục, phân quyền file.
3. **Google Calendar**: Xem, tạo, sửa, xóa sự kiện lịch.
4. **Google Docs**: Tạo, đọc, định dạng, thêm ghi chú tài liệu.
5. **Google Sheets**: Đọc/ghi ô, quản lý bảng tính, công thức.
6. **Google Slides**: Tạo và chỉnh sửa bài thuyết trình.
7. **Google Forms**: Tạo biểu mẫu và quản lý câu trả lời.
8. **Google Tasks**: Quản lý danh sách công việc.
9. **Google Contacts**: Tra cứu và quản lý danh bạ.
10. **Google Chat**: Gửi tin nhắn và quản lý không gian Chat.
11. **Apps Script**: Tự động hóa quy trình làm việc.
12. **Custom Search**: Tìm kiếm web lập trình.
