import os
import sys
import pytz
from datetime import datetime
from config import SERVICE_ACCOUNT_FILE, SPREADSHEET_ID

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

def get_sheets_service():
    """
    Authenticate with Google Sheets API using Service Account JSON credentials.
    """
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"⚠️ Không tìm thấy Service Account Key: {SERVICE_ACCOUNT_FILE}")
            return None

        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        service = build("sheets", "v4", credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Lỗi xác thực Google Sheets API: {e}")
        return None

def ensure_sheet_tabs_exist(sheets_service, spreadsheet_id: str):
    """
    Ensure the required worksheet tabs exist in the Google Spreadsheet.
    """
    try:
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_sheets = [s["properties"]["title"] for s in sheet_metadata.get("sheets", [])]

        required_tabs = ["Báo Cáo Giá DMX Hàng Ngày", "Lịch Sử Biến Động Giá"]
        requests = []

        for tab in required_tabs:
            if tab not in existing_sheets:
                requests.append({
                    "addSheet": {
                        "properties": {
                            "title": tab
                        }
                    }
                })

        if requests:
            body = {"requests": requests}
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()
            print(f"✨ Đã khởi tạo các Tab mới: {[r['addSheet']['properties']['title'] for r in requests]}")
    except Exception as e:
        print(f"⚠️ Cảnh báo khi tạo tab: {e}")

def update_daily_price_sheet(products: list[dict], spreadsheet_id: str = None) -> bool:
    """
    Update Tab 'Báo Cáo Giá DMX Hàng Ngày' with the latest scraped DMX prices.
    """
    spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
    service = get_sheets_service()
    if not service:
        print("❌ Không thể kết nối dịch vụ Google Sheets.")
        return False

    ensure_sheet_tabs_exist(service, spreadsheet_id)

    now_str = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")

    headers = [
        "STT",
        "Danh Mục",
        "Tên Sản Phẩm / Model",
        "Giá Niêm Yết (VND)",
        "Giá Bán Hiện Tại (VND)",
        "Giảm Giá (%)",
        "Trạng Thái",
        "Thời Gian Quét",
        "Khuyến Mãi Chi Tiết",
        "Link Sản Phẩm DMX"
    ]

    rows = [headers]
    for idx, p in enumerate(products, 1):
        rows.append([
            idx,
            p.get("category", "N/A"),
            p.get("name", "N/A"),
            p.get("mrp_price", 0),
            p.get("selling_price", 0),
            f"-{p.get('discount_pct', 0.0)}%",
            p.get("status", "đang kinh doanh"),
            now_str,
            p.get("promotions", "Không có"),
            p.get("url", "")
        ])

    # Summary row
    rows.append([
        "",
        "TỔNG THỐNG KÊ",
        f"Tổng {len(products)} sản phẩm",
        "=SUM(D2:D" + str(len(products)+1) + ")",
        "=SUM(E2:E" + str(len(products)+1) + ")",
        "=AVERAGE(F2:F" + str(len(products)+1) + ")",
        now_str,
        "",
        "",
        ""
    ])

    try:
        body = {"values": rows}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="'Báo Cáo Giá DMX Hàng Ngày'!A1:J" + str(len(rows) + 5),
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

        print(f"\n📊 [Google Sheets] ✅ Đã cập nhật thành công {len(products)} sản phẩm lên Sheet!")
        print(f"👉 Xem tại: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        return True
    except Exception as e:
        print(f"❌ Lỗi ghi dữ liệu Google Sheets: {e}")
        return False

def append_price_history_log(discounted_products: list[dict], spreadsheet_id: str = None) -> bool:
    """
    Append price drop alert events into Tab 'Lịch Sử Biến Động Giá'.
    """
    if not discounted_products:
        return True

    spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
    service = get_sheets_service()
    if not service:
        return False

    ensure_sheet_tabs_exist(service, spreadsheet_id)
    now_str = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for p in discounted_products:
        rows.append([
            now_str,
            p.get("category", "N/A"),
            p.get("name", "N/A"),
            p.get("mrp_price", 0),
            p.get("selling_price", 0),
            f"-{p.get('discount_pct', 0.0)}%",
            p.get("status", "giảm giá mạnh"),
            p.get("url", "")
        ])

    try:
        body = {"values": rows}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="'Lịch Sử Biến Động Giá'!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"📈 [Google Sheets] ✅ Đã lưu {len(rows)} sản phẩm giảm giá vào 'Lịch Sử Biến Động Giá'.")
        return True
    except Exception as e:
        print(f"⚠️ Lỗi append history log: {e}")
        return False

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_sample = [
            {
                "category": "Máy Lọc Không Khí",
                "name": "Máy lọc không khí LG PuriCare 360 Hit AS60GHWG0",
                "mrp_price": 7500000,
                "selling_price": 5990000,
                "discount_pct": 20.1,
                "status": "đang kinh doanh",
                "promotions": "Tặng PMH 200k",
                "url": "https://www.dienmayxanh.com/may-loc-khong-khi/lg-puricare-360-hit-as60ghwg0"
            }
        ]
        update_daily_price_sheet(test_sample)
