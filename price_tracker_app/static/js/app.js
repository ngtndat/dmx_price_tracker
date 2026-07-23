/* ===================================================================
   PricePulse – app.js
   Main JavaScript: Auth, Product CRUD, Chart, Tabs, Affiliate UX
   =================================================================== */

'use strict';

// ===== State =====
let currentUser   = null;
let authToken     = null;
let allProducts   = [];
let currentTab    = 'all';
let activeChart   = null;
let currentModalProduct = null;
let affiliateClickCount = 0;

// Platform URL examples
const EXAMPLE_URLS = {
    shopee:    'https://shopee.vn/Apple-AirPods-Pro-2nd-Generation-USB-C-i.1040956728.25680813978',
    lazada:    'https://www.lazada.vn/products/samsung-galaxy-s24-ultra-i4069847565-s20977199453.html',
    tiktok:    'https://www.tiktok.com/t/ZT8kxaT5s/',
    traveloka: 'https://www.traveloka.com/vi-vn/hotel/vietnam/ho-chi-minh-city-1659',
    trip:      'https://vn.trip.com/hotels/ho-chi-minh-city-hotel-detail-1535631/vinpearl-luxury-landmark-81/',
};

const PLATFORM_LABELS = {
    shopee:        { label: 'Shopee',          emoji: '🛒' },
    lazada:        { label: 'Lazada',          emoji: '🟠' },
    tiktok:        { label: 'TikTok Shop',     emoji: '🎵' },
    traveloka:     { label: 'Traveloka',       emoji: '✈️' },
    trip:          { label: 'Trip.com',        emoji: '🏨' },
    sendo:         { label: 'Sendo',           emoji: '🛍️' },
    thegioididong: { label: 'TGDĐ',           emoji: '📱' },
    dienmayxanh:   { label: 'Điện Máy Xanh',  emoji: '⚡' },
    bachhoaxanh:   { label: 'Bách Hoá Xanh',  emoji: '🛒' },
    cellphones:    { label: 'CellphoneS',      emoji: '📞' },
    tiki:          { label: 'Tiki',            emoji: '📦' },
    other:         { label: 'Khác',           emoji: '🔗' },
};

// ===================================================================
// UTILITIES
// ===================================================================

function formatVND(amount) {
    if (!amount && amount !== 0) return '—';
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
}

function formatDate(isoString) {
    if (!isoString) return '—';
    try {
        return new Intl.DateTimeFormat('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        }).format(new Date(isoString));
    } catch { return isoString.slice(0, 16).replace('T', ' '); }
}

function formatDateShort(isoString) {
    if (!isoString) return '—';
    try {
        return new Intl.DateTimeFormat('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            day: '2-digit', month: '2-digit',
        }).format(new Date(isoString));
    } catch { return '—'; }
}

function detectPlatform(url) {
    if (!url) return null;
    const u = url.toLowerCase();
    const MAP = {
        'shopee.vn': 'shopee', 'shope.ee': 'shopee',
        'lazada.vn': 'lazada', 'lzd.co': 'lazada',
        'tiktok.com': 'tiktok', 'tiktokshop.com': 'tiktok',
        'traveloka.com': 'traveloka',
        'trip.com': 'trip', 'ctrip.com': 'trip',
        'sendo.vn': 'sendo',
        'thegioididong.com': 'thegioididong',
        'dienmayxanh.com': 'dienmayxanh',
        'bachhoaxanh.com': 'bachhoaxanh',
        'cellphones.com.vn': 'cellphones',
        'tiki.vn': 'tiki',
    };
    for (const [domain, platform] of Object.entries(MAP)) {
        if (u.includes(domain)) return platform;
    }
    return 'other';
}

function showToast(msg, type = 'info', duration = 3500) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = `toast ${type} show`;
    setTimeout(() => { toast.className = 'toast'; }, duration);
}

function apiHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
    };
}

async function apiCall(method, path, body = null) {
    const opts = { method, headers: apiHeaders() };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
}

// ===================================================================
// AUTH
// ===================================================================

function initGoogleSignIn() {
    if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID === '') return;
    try {
        window.google?.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleCredential,
        });
        window.google?.accounts.id.renderButton(
            document.getElementById('google-signin-btn'),
            { theme: 'filled_black', size: 'medium', text: 'signin_with', shape: 'pill' }
        );
    } catch (e) {
        console.warn('Google Sign-In init failed:', e);
    }
}

async function handleGoogleCredential(response) {
    try {
        const data = await apiCall('POST', '/api/auth/google', { credential: response.credential });
        setUser(data.user, response.credential);
    } catch (e) {
        showToast('Đăng nhập thất bại: ' + e.message, 'error');
    }
}

async function handleSandboxLogin(userId) {
    if (!userId) return;
    const token = `mock_token_${userId}`;
    try {
        const data = await apiCall('POST', '/api/auth/google', { credential: token });
        setUser(data.user, token);
        document.getElementById('sandbox-user').value = '';
    } catch (e) {
        showToast('Sandbox login thất bại: ' + e.message, 'error');
    }
}

function setUser(user, token) {
    currentUser = user;
    authToken = token;

    // Update UI
    const chip = document.getElementById('user-chip');
    document.getElementById('user-avatar').src = user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=6366f1&color=fff&size=80`;
    document.getElementById('user-display-name').textContent = user.name || user.email;
    chip.style.display = 'flex';
    document.getElementById('google-signin-btn').style.display = 'none';
    document.getElementById('sandbox-wrap').style.display = 'none';

    // Show logged-in panels
    document.getElementById('login-prompt').style.display = 'none';
    document.getElementById('input-panel').style.display = 'block';
    document.getElementById('products-section').style.display = 'block';
    document.getElementById('stats-card').style.display = 'block';

    loadProducts();
    loadStats();
}

function logout() {
    currentUser = null;
    authToken = null;
    allProducts = [];
    document.getElementById('user-chip').style.display = 'none';
    document.getElementById('google-signin-btn').style.display = 'block';
    document.getElementById('sandbox-wrap').style.display = 'block';
    document.getElementById('login-prompt').style.display = 'block';
    document.getElementById('input-panel').style.display = 'none';
    document.getElementById('products-section').style.display = 'none';
    document.getElementById('stats-card').style.display = 'none';
    document.getElementById('product-grid').innerHTML = '';
    showToast('Đã đăng xuất', 'info');
}

// ===================================================================
// PRODUCTS
// ===================================================================

async function loadProducts() {
    try {
        allProducts = await apiCall('GET', '/api/products');
        renderProducts();
    } catch (e) {
        showToast('Lỗi tải sản phẩm: ' + e.message, 'error');
    }
}

async function loadStats() {
    try {
        const stats = await apiCall('GET', '/api/stats');
        document.getElementById('stat-total').textContent  = stats.active ?? 0;
        document.getElementById('stat-at-lowest').textContent = stats.at_lowest ?? 0;
        document.getElementById('stat-dead').textContent   = stats.dead ?? 0;
        document.getElementById('stat-clicks').textContent = stats.affiliate_clicks ?? 0;
    } catch (e) {
        console.warn('Stats error:', e);
    }
}

// ===================================================================
// TRACK FORM
// ===================================================================

// Real-time platform detection in URL field
document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('product-url');
    if (urlInput) {
        urlInput.addEventListener('input', () => {
            const platform = detectPlatform(urlInput.value);
            const badge = document.getElementById('platform-detect-badge');
            const strip = document.getElementById('aff-tip-strip');
            const tipText = document.getElementById('aff-tip-text');
            if (platform && platform !== 'other' && urlInput.value.length > 10) {
                const info = PLATFORM_LABELS[platform] || {};
                badge.textContent = `${info.emoji || ''} ${info.label || platform}`;
                badge.className = `platform-detect-badge visible platform-badge ${platform}`;
                // Show affiliate tip
                if (strip && tipText) {
                    tipText.innerHTML = getAffiliateTipHTML(platform);
                    strip.style.display = 'flex';
                }
            } else {
                badge.className = 'platform-detect-badge';
                if (strip) strip.style.display = 'none';
            }
        });
    }

    initGoogleSignIn();
});

function getAffiliateTipHTML(platform) {
    const tips = {
        shopee:    `💡 Đăng ký <a href="https://affiliate.shopee.vn" target="_blank">Shopee Affiliate</a> hoặc <a href="https://accesstrade.vn" target="_blank">AccessTrade</a> để nhận hoa hồng 3–8% mỗi đơn hàng.`,
        lazada:    `💡 Đăng ký <a href="https://accesstrade.vn" target="_blank">AccessTrade</a> để tạo deep link Lazada và nhận hoa hồng 2–5%.`,
        tiktok:    `💡 Tham gia <a href="https://accesstrade.vn" target="_blank">AccessTrade</a> để nhận hoa hồng từ TikTok Shop.`,
        traveloka: `💡 Đăng ký <a href="https://www.traveloka.com/vi-vn/p/affiliate" target="_blank">Traveloka Affiliate</a> để nhận hoa hồng cho mỗi booking.`,
        trip:      `💡 Tham gia <a href="https://affiliates.trip.com" target="_blank">Trip.com Affiliate</a> để nhận hoa hồng từ đặt phòng và tour.`,
    };
    return tips[platform] || `💡 Đăng ký <a href="https://accesstrade.vn" target="_blank">AccessTrade</a> để kiếm hoa hồng từ link này!`;
}

function fillExample(platform) {
    const urlInput = document.getElementById('product-url');
    if (urlInput && EXAMPLE_URLS[platform]) {
        urlInput.value = EXAMPLE_URLS[platform];
        urlInput.dispatchEvent(new Event('input'));
        urlInput.focus();
    }
}

async function handleTrackProduct(event) {
    event.preventDefault();
    const urlInput  = document.getElementById('product-url');
    const btnText   = document.getElementById('btn-track-text');
    const spinner   = document.getElementById('btn-spinner');
    const btn       = document.getElementById('btn-track');

    const url = urlInput.value.trim();
    if (!url) return;

    btn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'block';

    try {
        const product = await apiCall('POST', '/api/products', { url });
        allProducts.unshift(product);
        renderProducts();
        urlInput.value = '';
        document.getElementById('platform-detect-badge').className = 'platform-detect-badge';
        document.getElementById('aff-tip-strip').style.display = 'none';
        showToast(`✅ Đã thêm: ${product.title.substring(0, 40)}...`, 'success');
        loadStats();
    } catch (e) {
        showToast(`❌ ${e.message}`, 'error', 5000);
    } finally {
        btn.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

// ===================================================================
// TABS & RENDERING
// ===================================================================

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    renderProducts();
}

function getFilteredProducts() {
    switch (currentTab) {
        case 'deal':
            return allProducts.filter(p =>
                p.is_active && p.lowest_price && p.current_price <= p.lowest_price
            );
        case 'dead':
            return allProducts.filter(p => !p.is_active);
        default:
            return allProducts;
    }
}

function renderProducts() {
    const grid   = document.getElementById('product-grid');
    const empty  = document.getElementById('empty-state');
    const filtered = getFilteredProducts();

    // Update tab badges
    const all  = allProducts;
    const deal = all.filter(p => p.is_active && p.lowest_price && p.current_price <= p.lowest_price);
    const dead = all.filter(p => !p.is_active);
    document.getElementById('tab-badge-all').textContent  = all.length;
    document.getElementById('tab-badge-deal').textContent = deal.length;
    document.getElementById('tab-badge-dead').textContent = dead.length;

    if (filtered.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';
    grid.innerHTML = filtered.map(buildProductCard).join('');
}

function buildProductCard(p) {
    const isDead = !p.is_active;
    const isDeal = !isDead && p.lowest_price && p.current_price <= p.lowest_price;
    const pInfo  = PLATFORM_LABELS[p.platform] || PLATFORM_LABELS.other;

    // Price change
    const history_first = p.lowest_price !== undefined ? null : null; // will compute from API when chart opens
    let changeHTML = '';
    if (p.highest_price && p.current_price < p.highest_price) {
        const diff = p.current_price - p.highest_price;
        const pct  = ((diff / p.highest_price) * 100).toFixed(1);
        changeHTML = `<span class="price-change-badge down">${pct}%</span>`;
    }

    const deadOverlay = isDead ? `<div class="dead-overlay"><span class="dead-overlay-text">☠️ Link đã chết</span></div>` : '';
    const dealBadge   = isDeal ? `<span class="deal-badge">🔥 GIÁ THẤP NHẤT</span>` : '';

    const lowestHTML  = p.lowest_price  ? `<span>📉 Thấp: ${formatVND(p.lowest_price)}</span>`  : '';
    const highestHTML = p.highest_price ? `<span>📈 Cao: ${formatVND(p.highest_price)}</span>` : '';

    const imgSrc = p.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=400&h=400&q=80';

    const affiliateUrl = `/redirect?url=${encodeURIComponent(p.original_url)}&product_id=${p.id}&platform=${p.platform}`;

    return `
    <div class="product-card ${isDead ? 'is-dead' : ''} ${isDeal ? 'is-deal' : ''}" id="card-${p.id}">
        ${deadOverlay}
        <div class="card-img-wrap">
            <img src="${imgSrc}" alt="${p.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=400&h=400&q=80'">
            <span class="platform-badge ${p.platform}">${pInfo.emoji} ${pInfo.label}</span>
            ${dealBadge}
        </div>
        <div class="card-body">
            <h4 class="card-title-text" title="${p.title}">${p.title}</h4>
            <div class="price-row">
                <span class="price-current ${isDeal ? 'down' : ''}">${formatVND(p.current_price)}</span>
                ${changeHTML}
            </div>
            <div class="price-meta">
                ${lowestHTML}
                ${highestHTML}
            </div>
            <div class="card-date-row">
                <span>📅 Theo dõi từ: ${formatDateShort(p.created_at)}</span>
                <span>🕐 Cập nhật: ${formatDate(p.last_checked_at || p.created_at)}</span>
            </div>
        </div>
        <div class="card-actions">
            <button class="btn-card" onclick="openChartModal(${p.id})" ${isDead ? 'disabled' : ''} title="Xem lịch sử giá">
                📊 Lịch sử giá
            </button>
            <button class="btn-card" onclick="refreshPrice(${p.id})" ${isDead ? 'disabled' : ''} title="Làm mới giá ngay">
                🔄 Làm mới
            </button>
            <a class="btn-card primary" href="${affiliateUrl}" target="_blank"
               onclick="logAffiliateClick(${p.id}, '${p.platform}')">
                🛒 Mua ngay
            </a>
            <button class="btn-card danger" onclick="deleteProduct(${p.id})" title="Xóa khỏi danh sách">
                🗑️ Xóa
            </button>
        </div>
    </div>`;
}

// ===================================================================
// PRICE REFRESH
// ===================================================================

async function refreshPrice(productId) {
    const card = document.getElementById(`card-${productId}`);
    if (card) card.style.opacity = '0.5';
    try {
        const result = await apiCall('POST', `/api/products/${productId}/refresh`);
        if (result.status === 'dead') {
            showToast('☠️ Link sản phẩm đã die – ngừng theo dõi', 'error');
        } else {
            const pct  = result.change_pct;
            const sign = pct >= 0 ? '+' : '';
            const dir  = pct < 0 ? '📉' : '📈';
            showToast(`${dir} Giá cập nhật: ${formatVND(result.new_price)} (${sign}${pct}%)`, pct < 0 ? 'success' : 'info');
        }
        await loadProducts();
        await loadStats();
    } catch (e) {
        showToast('Lỗi làm mới: ' + e.message, 'error');
    } finally {
        if (card) card.style.opacity = '1';
    }
}

// ===================================================================
// DELETE PRODUCT
// ===================================================================

async function deleteProduct(productId) {
    if (!confirm('Bạn có chắc muốn ngừng theo dõi sản phẩm này không?')) return;
    try {
        await apiCall('DELETE', `/api/products/${productId}`);
        allProducts = allProducts.filter(p => p.id !== productId);
        renderProducts();
        loadStats();
        showToast('✅ Đã xóa sản phẩm', 'info');
    } catch (e) {
        showToast('Lỗi xóa: ' + e.message, 'error');
    }
}

// ===================================================================
// AFFILIATE CLICK LOG
// ===================================================================

async function logAffiliateClick(productId, platform) {
    if (!authToken) return;
    try {
        await apiCall('POST', '/api/affiliate/click', { product_id: productId, platform });
    } catch { /* silent */ }
}

// Called from modal Buy Now button
function logAffiliate() {
    if (currentModalProduct) {
        logAffiliateClick(currentModalProduct.id, currentModalProduct.platform);
    }
}

// ===================================================================
// CHART MODAL
// ===================================================================

async function openChartModal(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;
    currentModalProduct = product;

    // Populate modal header
    const pInfo = PLATFORM_LABELS[product.platform] || PLATFORM_LABELS.other;
    const badge = document.getElementById('modal-platform-badge');
    badge.textContent = `${pInfo.emoji} ${pInfo.label}`;
    badge.className = `platform-badge-modal platform-badge ${product.platform}`;

    document.getElementById('modal-title').textContent = product.title;
    const urlShort = product.original_url.replace(/^https?:\/\//, '').split('?')[0].substring(0, 60) + '...';
    document.getElementById('modal-url-short').textContent = urlShort;

    // Stats
    document.getElementById('ms-current').textContent = formatVND(product.current_price);
    document.getElementById('ms-lowest').textContent  = formatVND(product.lowest_price);
    document.getElementById('ms-highest').textContent = formatVND(product.highest_price);

    // Buy link (affiliate)
    const buyLink = document.getElementById('modal-buy-link');
    buyLink.href = `/redirect?url=${encodeURIComponent(product.original_url)}&product_id=${product.id}&platform=${product.platform}`;

    // Show modal
    document.getElementById('chart-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Load history
    try {
        const history = await apiCall('GET', `/api/products/${productId}/history`);

        // Start & change stats
        if (history.length > 0) {
            const startPrice = history[0].price;
            const endPrice   = history[history.length - 1].price;
            const diff       = endPrice - startPrice;
            const diffPct    = startPrice ? ((diff / startPrice) * 100).toFixed(1) : 0;
            document.getElementById('ms-start').textContent  = formatVND(startPrice);
            const changeEl = document.getElementById('ms-change');
            changeEl.textContent = `${diff >= 0 ? '+' : ''}${formatVND(diff)} (${diff >= 0 ? '+' : ''}${diffPct}%)`;
            changeEl.className = `ms-val ${diff < 0 ? 'text-green' : diff > 0 ? 'text-red' : ''}`;
        }

        renderPriceChart(history);
    } catch (e) {
        showToast('Lỗi tải lịch sử giá: ' + e.message, 'error');
    }
}

function renderPriceChart(history) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    if (activeChart) { activeChart.destroy(); activeChart = null; }

    if (!history || history.length === 0) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        return;
    }

    const labels = history.map(h => formatDateShort(h.recorded_at));
    const prices = history.map(h => h.price);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);

    activeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Giá (VND)',
                data: prices,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99,102,241,0.12)',
                borderWidth: 2.5,
                pointRadius: history.length < 30 ? 4 : 2,
                pointHoverRadius: 6,
                pointBackgroundColor: prices.map(p =>
                    p === minP ? '#34d399' : p === maxP ? '#f87171' : '#6366f1'
                ),
                fill: true,
                tension: 0.35,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1a2035',
                    titleColor: '#94a3b8',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(99,102,241,0.4)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: ctx => '  ' + formatVND(ctx.parsed.y),
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b', font: { size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: {
                        color: '#64748b', font: { size: 11 },
                        callback: v => {
                            if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M';
                            if (v >= 1_000)     return (v / 1_000).toFixed(0) + 'K';
                            return v;
                        }
                    }
                }
            },
            animation: { duration: 600, easing: 'easeInOutCubic' }
        }
    });
}

function closeChartModal() {
    document.getElementById('chart-modal').style.display = 'none';
    document.body.style.overflow = '';
    if (activeChart) { activeChart.destroy(); activeChart = null; }
    currentModalProduct = null;
}

function handleModalOverlayClick(event) {
    if (event.target === document.getElementById('chart-modal')) {
        closeChartModal();
    }
}

// Close modal on Escape key
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeChartModal();
});
