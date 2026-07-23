import os
import random
import urllib.parse
import requests
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database
import scraper
import affiliate as aff
import scheduler as sched
from config import Config

app = FastAPI(
    title="PricePulse – E-Commerce Price Tracker API",
    description="Theo dõi giá sản phẩm thương mại điện tử tự động, cập nhật mỗi 6 giờ (GMT+7)",
    version="2.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Lifecycle ---

_scheduler_instance = None

@app.on_event("startup")
def startup_event():
    global _scheduler_instance
    database.init_db()
    _scheduler_instance = sched.start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.shutdown(wait=False)
        print("[App] Scheduler stopped.")

# --- Auth Dependency ---

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ")[1]

    # Sandbox/mock token handling (developer convenience)
    if token.startswith("mock_token_"):
        user_id = token.replace("mock_token_", "")
        email = f"{user_id}@demo.pricepulse.vn"
        name = f"Demo User ({user_id.replace('_', ' ').title()})"
        picture = f"https://ui-avatars.com/api/?name={urllib.parse.quote(name)}&background=6366f1&color=fff&size=80"

        user = database.get_user(user_id)
        if not user:
            user = database.create_user(user_id, email, name, picture)
        return user

    # Real Google OAuth verify
    try:
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}",
            timeout=5
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Google token verification failed")

        token_info = response.json()

        if Config.GOOGLE_CLIENT_ID and token_info.get("aud") != Config.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Google token client ID mismatch")

        user_id = token_info.get("sub")
        email = token_info.get("email")
        name = token_info.get("name")
        picture = token_info.get("picture")

        user = database.get_user(user_id)
        if not user:
            user = database.create_user(user_id, email, name, picture)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

# --- Pydantic Models ---

class TokenLoginRequest(BaseModel):
    credential: str

class TrackProductRequest(BaseModel):
    url: str

class AffiliateClickRequest(BaseModel):
    product_id: int
    platform: str

# ============================================================
# API Routes
# ============================================================

@app.post("/api/auth/google")
def auth_google(payload: TokenLoginRequest):
    """Validates Google ID token or processes developer sandbox mock login."""
    token = payload.credential

    if token.startswith("mock_token_"):
        user_id = token.replace("mock_token_", "")
        email = f"{user_id}@demo.pricepulse.vn"
        name = f"Demo User ({user_id.replace('_', ' ').title()})"
        picture = f"https://ui-avatars.com/api/?name={urllib.parse.quote(name)}&background=6366f1&color=fff&size=80"
        user = database.create_user(user_id, email, name, picture)
        return {"status": "success", "user": user, "token": token}

    try:
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}",
            timeout=5
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google token")

        token_info = response.json()
        user = database.create_user(
            token_info.get("sub"),
            token_info.get("email"),
            token_info.get("name"),
            token_info.get("picture")
        )
        return {"status": "success", "user": user, "token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token verification error: {str(e)}")


@app.get("/api/products")
def get_products(current_user: dict = Depends(get_current_user)):
    """Returns user's tracked products list (active + inactive)."""
    products = database.get_user_products(current_user["id"])
    # Attach affiliate tip for each product
    for p in products:
        p["affiliate_tip"] = aff.get_affiliate_setup_tip(p["platform"])
    return products


@app.post("/api/products")
def add_product(payload: TrackProductRequest, current_user: dict = Depends(get_current_user)):
    """Adds a product link to track. Scrapes metadata from the target URL."""
    url = payload.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="URL không hợp lệ. Phải bắt đầu bằng http:// hoặc https://")

    try:
        product_info = scraper.scrape_product_info(url)

        if product_info.get("is_dead"):
            raise HTTPException(
                status_code=422,
                detail="Link sản phẩm không còn tồn tại hoặc đã bị xóa. Vui lòng kiểm tra lại URL."
            )

        db_product = database.add_product(
            user_id=current_user["id"],
            platform=product_info["platform"],
            original_url=product_info["original_url"],
            title=product_info["title"],
            image_url=product_info["image_url"],
            current_price=product_info["current_price"]
        )
        db_product["affiliate_tip"] = aff.get_affiliate_setup_tip(db_product["platform"])
        return db_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi cào dữ liệu sản phẩm: {str(e)}")


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, current_user: dict = Depends(get_current_user)):
    """Deletes a product from user tracking list."""
    success = database.delete_product(product_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Sản phẩm không tìm thấy hoặc bạn không có quyền xóa")
    return {"status": "success", "message": "Đã ngừng theo dõi sản phẩm"}


@app.get("/api/products/{product_id}/history")
def get_product_history(product_id: int, current_user: dict = Depends(get_current_user)):
    """Gets price history points for chart rendering."""
    product = database.get_product(product_id)
    if not product or product["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    return database.get_price_history(product_id)


@app.post("/api/products/{product_id}/refresh")
def refresh_product_price(product_id: int, current_user: dict = Depends(get_current_user)):
    """
    Manually refreshes price for a product.
    For simulated products: applies +/- 5–15% fluctuation to demo price history charts.
    For real products: re-scrapes the live URL.
    """
    product = database.get_product(product_id)
    if not product or product["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    if not product.get("is_active"):
        raise HTTPException(status_code=409, detail="Sản phẩm đã ngừng theo dõi vì link đã chết")

    old_price = product["current_price"]

    try:
        # For demo / simulated products
        if product["title"].startswith("[") and "]" in product["title"]:
            change_pct = random.choice([-0.12, -0.08, -0.05, -0.03, 0.03, 0.05, 0.08, 0.12])
            new_price = max(10000, int(old_price * (1 + change_pct)))
        else:
            scraped = scraper.scrape_product_info(product["original_url"])
            if scraped.get("is_dead"):
                database.mark_product_dead(product_id)
                return {"status": "dead", "message": "Link sản phẩm đã chết, ngừng theo dõi"}
            new_price = scraped.get("current_price", old_price)

        database.update_product_price(product_id, new_price)
        change = new_price - old_price
        change_pct = (change / old_price * 100) if old_price else 0
        return {
            "status": "success",
            "old_price": old_price,
            "new_price": new_price,
            "change": change,
            "change_pct": round(change_pct, 2)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi làm mới giá: {str(e)}")


@app.post("/api/affiliate/click")
def log_affiliate_click(payload: AffiliateClickRequest, current_user: dict = Depends(get_current_user)):
    """Logs an affiliate link click for analytics."""
    database.log_affiliate_click(payload.product_id, current_user["id"], payload.platform)
    return {"status": "logged"}


@app.get("/api/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    """Returns dashboard stats for the current user."""
    products = database.get_user_products(current_user["id"])
    active = [p for p in products if p.get("is_active")]
    dead = [p for p in products if not p.get("is_active")]
    discounted = [
        p for p in active
        if p.get("lowest_price") and p["current_price"] <= p["lowest_price"]
    ]
    return {
        "total": len(products),
        "active": len(active),
        "dead": len(dead),
        "at_lowest": len(discounted),
        "affiliate_clicks": database.get_affiliate_click_count(),
    }


@app.get("/api/scheduler/status")
def get_scheduler_status():
    """Returns next scheduled price check time."""
    global _scheduler_instance
    if not _scheduler_instance:
        return {"status": "not_running"}
    jobs = _scheduler_instance.get_jobs()
    result = []
    for job in jobs:
        result.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })
    return {"status": "running", "jobs": result}


@app.get("/redirect")
def affiliate_redirect(url: str, product_id: int = None, platform: str = "other"):
    """
    Affiliate redirect gate. Converts URL to affiliate link and redirects.
    Logs click for analytics.
    """
    target_url = urllib.parse.unquote(url)
    detected_platform = scraper.analyze_url(target_url) if platform == "other" else platform
    affiliate_result = aff.convert_to_affiliate(target_url, detected_platform)

    print(f"[Affiliate] Click → platform={detected_platform} | network={affiliate_result['network']} | converted={affiliate_result['is_converted']}")

    return RedirectResponse(url=affiliate_result["affiliate_url"])


# ============================================================
# Static File Serving
# ============================================================

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def read_root():
    static_index = os.path.join(static_dir, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return JSONResponse({"message": "PricePulse API is running. Frontend not found in /static/"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=True)
