/**
 * LG AR SpaceVision — app.js v6
 * High-performance mobile AR & 3D WebViewer
 * - Full-card tap support for seamless mobile interaction
 * - Cache-busted products.json fetching
 * - Real-time progress bar with percent indicator
 * - Wall & Floor intelligent surface detection
 */

const state = {
  products: [],
  filteredProducts: [],
  selectedProduct: null,
};

const $ = id => document.getElementById(id);

// ─── Init ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await loadProducts();
  setupFilters();
  setupModals();
  setupModelViewerEvents();
});

// ─── Load products.json (with cache buster) ──────
async function loadProducts() {
  try {
    const r = await fetch('products.json?v=' + Date.now());
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    state.products = await r.json();
    state.filteredProducts = [...state.products];
    renderProducts();
  } catch (e) {
    console.error('products.json load failed:', e);
    const grid = $('productsGrid');
    if (grid) {
      grid.innerHTML = `<div class="empty-state"><i class="bi bi-exclamation-triangle"></i><p>Không thể tải danh sách sản phẩm: ${e.message}</p></div>`;
    }
  }
}

// ─── Render cards ────────────────────────────────
function renderProducts() {
  const grid = $('productsGrid');
  if (!grid) return;
  grid.innerHTML = '';

  if (!state.filteredProducts.length) {
    grid.innerHTML = `<div class="empty-state"><i class="bi bi-inbox"></i><p>Không tìm thấy sản phẩm phù hợp.</p></div>`;
    return;
  }

  state.filteredProducts.forEach(prod => {
    const card = document.createElement('div');
    card.className = 'product-card';
    const thumb = prod.images?.front || Object.values(prod.images || {}).find(v => v) || null;
    const isWall = prod.placement === 'wall';
    const hasGLB = !!prod.glbFile;
    const sizeMB = prod.glbSizeMB || null;
    const isComingSoon = prod.status === 'coming_soon';

    // Thumbnail: image or themed placeholder
    const thumbHtml = thumb
      ? `<img src="${thumb}" alt="${prod.name}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
         <div class="thumb-placeholder" style="display:none"><i class="bi bi-box-seam"></i></div>`
      : `<div class="thumb-placeholder"><i class="bi bi-${isWall ? 'wind' : 'tornado'}"></i></div>`;

    // Action buttons vs Coming Soon status
    const actionHtml = isComingSoon
      ? `<div class="card-coming-soon">
           <i class="bi bi-clock-history"></i> Sản phẩm đang phát triển thêm mô hình 3D
         </div>`
      : `<div class="card-actions">
           <button class="btn-ar btn-ar-launch">
             <i class="bi bi-camera-fill"></i> Thử AR Trong Phòng
           </button>
           <button class="btn-3d btn-3d-view">
             <i class="bi bi-box-seam"></i> Xem 3D 360°
           </button>
         </div>`;

    card.innerHTML = `
      <div class="card-thumb" style="cursor:${isComingSoon ? 'default' : 'pointer'}">
        <span class="card-placement-badge ${isComingSoon ? 'coming-soon' : (isWall ? 'wall' : '')}">
          <i class="bi bi-${isComingSoon ? 'hourglass-split' : (isWall ? 'layout-wtf' : 'grid')}"></i>
          ${isComingSoon ? 'Sắp ra mắt' : (isWall ? 'Treo tường (Wall)' : 'Đặt sàn (Floor)')}
        </span>
        ${hasGLB ? `<span class="card-glb-badge"><i class="bi bi-box"></i> 3D GLB ${sizeMB ? `(${sizeMB}MB)` : ''}</span>` : ''}
        ${thumbHtml}
      </div>
      <div class="card-body">
        <div class="card-cat">${prod.category}</div>
        <div class="card-name" style="cursor:${isComingSoon ? 'default' : 'pointer'}">${prod.name}</div>
        <div class="card-specs">
          <div class="spec"><span class="spec-label">Cao</span><span class="spec-val">${prod.dimensions?.height ?? '?'} cm</span></div>
          <div class="spec"><span class="spec-label">Ngang</span><span class="spec-val">${prod.dimensions?.width ?? '?'} cm</span></div>
          <div class="spec"><span class="spec-label">Sâu</span><span class="spec-val">${prod.dimensions?.depth ?? '?'} cm</span></div>
        </div>
        ${actionHtml}
      </div>`;

    // Card click behavior
    if (!isComingSoon) {
      // Tap on card thumb / title / body opens viewer
      card.querySelector('.card-thumb').addEventListener('click', () => openViewer(prod));
      card.querySelector('.card-name').addEventListener('click', () => openViewer(prod));
      card.querySelector('.btn-ar-launch').addEventListener('click', e => {
        e.stopPropagation();
        openViewer(prod);
      });
      card.querySelector('.btn-3d-view').addEventListener('click', e => {
        e.stopPropagation();
        openViewer(prod);
      });
    }

    grid.appendChild(card);
  });
}

// ─── Open viewer modal ───────────────────────────
async function openViewer(product) {
  state.selectedProduct = product;
  const mv = $('modelViewer');
  const isWall = product.placement === 'wall';

  // Update header info
  $('arModalTitle').textContent = product.name;
  $('scaleBadge').innerHTML = `
    <i class="bi bi-rulers"></i>
    Kích thước chuẩn: ${product.dimensions?.height}H × ${product.dimensions?.width}W × ${product.dimensions?.depth}D cm (Tỉ lệ 1:1)`;

  // Placement guidance
  const tip = $('scanTip');
  tip.className = `scan-tip ${isWall ? 'wall' : 'floor'}`;
  $('scanTipText').innerHTML = isWall
    ? `<strong>Sản phẩm treo tường</strong>: Hướng camera vào <strong>BỨC TƯỜNG</strong>, di chuyển chậm để quét mặt phẳng, rồi bấm <strong>Bật AR</strong>.`
    : `<strong>Sản phẩm đặt sàn</strong>: Hướng camera xuống <strong>MẶT SÀN</strong>, di chuyển chậm để quét mặt phẳng, rồi bấm <strong>Bật AR</strong>.`;

  // Set AR placement mode
  mv.setAttribute('ar-placement', isWall ? 'wall' : 'floor');
  mv.removeAttribute('orientation');

  // Open modal and show initial loading state
  $('arModal').classList.add('active');
  $('arUnavail').style.display = 'none';
  showLoading(true, 0);

  // Set 3D model source
  if (product.glbFile) {
    mv.setAttribute('src', product.glbFile);
  } else {
    try {
      const url = await generateFallbackGLB(product);
      mv.setAttribute('src', url);
    } catch (err) {
      console.error('Fallback GLB error:', err);
      showLoading(false);
      $('arUnavail').style.display = 'flex';
      $('arUnavail').innerHTML = `<i class="bi bi-exclamation-triangle"></i> Lỗi tạo mô hình 3D: ${err.message}`;
    }
  }
}

// ─── model-viewer events ─────────────────────────
function setupModelViewerEvents() {
  const mv = $('modelViewer');
  if (!mv) return;

  // Real-time download progress tracking
  mv.addEventListener('progress', e => {
    const progress = Math.round((e.detail.totalProgress || 0) * 100);
    showLoading(true, progress);
  });

  // Model successfully loaded and ready for rendering
  mv.addEventListener('load', () => {
    showLoading(false);
    const arBtn = $('arBtn');
    if (!mv.canActivateAR) {
      if (arBtn) arBtn.style.display = 'none';
      $('arUnavail').style.display = 'flex';
      $('arUnavail').innerHTML = `<i class="bi bi-info-circle"></i> Trình duyệt máy tính hỗ trợ xoay 360°. Để dùng AR camera, mở link trên Safari iPhone hoặc Chrome Android.`;
    } else {
      if (arBtn) arBtn.style.display = 'flex';
      $('arUnavail').style.display = 'none';
    }
  });

  // Model loading failure
  mv.addEventListener('error', e => {
    console.error('model-viewer error:', e);
    showLoading(false);
    $('arUnavail').style.display = 'flex';
    $('arUnavail').innerHTML = `<i class="bi bi-exclamation-triangle"></i> Không thể tải file mô hình 3D. Vui lòng kiểm tra kết nối mạng và thử lại.`;
  });

  // AR lifecycle state transitions
  mv.addEventListener('ar-status', e => {
    const arBtn = $('arBtn');
    const status = e.detail.status;
    if (status === 'session-started') {
      if (arBtn) arBtn.innerHTML = `<i class="bi bi-record-circle-fill"></i> AR đang hoạt động...`;
    } else if (status === 'not-presenting') {
      if (arBtn) arBtn.innerHTML = `<i class="bi bi-camera-fill"></i> Bật AR — Đặt vào phòng`;
    } else if (status === 'failed') {
      alert('Không thể khởi động AR.\n\n• Vui lòng cấp quyền Camera cho trình duyệt\n• Dùng Safari (iOS 15+) hoặc Chrome (Android có ARCore)\n• Đảm bảo truy cập qua giao thức HTTPS.');
      if (arBtn) arBtn.innerHTML = `<i class="bi bi-camera-fill"></i> Bật AR — Đặt vào phòng`;
    }
  });
}

function showLoading(show, percent = 0) {
  const el = $('mvLoading');
  if (!el) return;
  el.style.display = show ? 'flex' : 'none';
  if (show) {
    el.innerHTML = `
      <div class="mv-spinner"></div>
      <span style="font-weight:600;font-size:1rem;">Đang tải mô hình 3D... ${percent > 0 ? `${percent}%` : ''}</span>
      <div style="width:160px;height:4px;background:rgba(255,255,255,0.2);border-radius:2px;overflow:hidden;margin-top:4px;">
        <div style="width:${Math.max(percent, 5)}%;height:100%;background:#A50034;transition:width 0.2s ease;"></div>
      </div>
    `;
  }
}

// ─── Category filter ─────────────────────────────
function setupFilters() {
  document.querySelectorAll('.cat-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const cat = chip.dataset.category;
      state.filteredProducts = cat === 'all'
        ? [...state.products]
        : state.products.filter(p => p.categoryKey === cat);
      renderProducts();
    });
  });
}

// ─── Modal open/close ────────────────────────────
function setupModals() {
  $('arModalClose').addEventListener('click', closeARModal);
  $('arModal').addEventListener('click', e => {
    if (e.target === $('arModal')) closeARModal();
  });

  $('btnOpenUpload').addEventListener('click', () => $('uploadModal').classList.add('active'));
  $('uploadModalClose').addEventListener('click', () => $('uploadModal').classList.remove('active'));
  $('uploadModal').addEventListener('click', e => {
    if (e.target === $('uploadModal')) $('uploadModal').classList.remove('active');
  });

  $('addProductForm').addEventListener('submit', handleAddProduct);
}

function closeARModal() {
  $('arModal').classList.remove('active');
  const mv = $('modelViewer');
  if (mv) {
    mv.removeAttribute('src');
    mv.removeAttribute('ar-placement');
  }
  showLoading(false);
  const arBtn = $('arBtn');
  if (arBtn) arBtn.innerHTML = `<i class="bi bi-camera-fill"></i> Bật AR — Đặt vào phòng`;
}

// ─── Add product form ────────────────────────────
function handleAddProduct(e) {
  e.preventDefault();
  const f = $('addProductForm');
  const name = $('prodName').value.trim();
  const height = parseFloat($('prodHeight').value);
  const width  = parseFloat($('prodWidth').value);
  const depth  = parseFloat($('prodDepth').value);
  const placement = $('prodPlacement').value;
  const category  = $('prodCategory').value;

  if (!name || !height || !width || !depth) {
    alert('Vui lòng nhập đầy đủ tên và kích thước!');
    return;
  }

  const frontFile = $('imgFront').files[0];
  const frontUrl  = frontFile ? URL.createObjectURL(frontFile) : 'images/products/refrigerator_front.png';

  const catMap = {
    'Tủ lạnh': 'refrigerator', 'Máy giặt': 'washer',
    'TV OLED': 'tv', 'Máy lạnh': 'ac', 'Máy lọc KK': 'purifier'
  };

  const prod = {
    id: `custom-${Date.now()}`,
    name, category,
    categoryKey: catMap[category] || 'other',
    status: 'ready',
    placement,
    dimensions: { height, width, depth, unit: 'cm' },
    images: { front: frontUrl },
    description: 'Sản phẩm tạo mới.'
  };

  state.products.unshift(prod);
  state.filteredProducts = [...state.products];
  renderProducts();
  $('uploadModal').classList.remove('active');
  f.reset();
  openViewer(prod);
}

// ─── Fallback box GLB (Three.js generated for dimension preview) ──
function makeMat(tex) {
  return tex
    ? new THREE.MeshStandardMaterial({ map: tex, transparent: true, alphaTest: 0.1, metalness: 0.2, roughness: 0.3 })
    : new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.5, roughness: 0.3 });
}

async function generateFallbackGLB(product) {
  if (typeof THREE === 'undefined' || !THREE.GLTFExporter) throw new Error('Three.js not loaded');

  return new Promise((resolve, reject) => {
    const W = (product.dimensions?.width  || 60) / 100;
    const H = (product.dimensions?.height || 100) / 100;
    const D = (product.dimensions?.depth  || 50) / 100;

    const loader = new THREE.TextureLoader();
    const imgs = product.images || {};
    const load = p => p ? loader.load(p) : null;

    const geo = new THREE.BoxGeometry(W, H, D);
    const mats = [
      makeMat(load(imgs.right)), makeMat(load(imgs.left)),
      makeMat(load(imgs.top)),   makeMat(null),
      makeMat(load(imgs.front)), makeMat(load(imgs.back)),
    ];

    const mesh = new THREE.Mesh(geo, mats);
    mesh.position.y = H / 2;
    const scene = new THREE.Scene();
    scene.add(mesh);
    scene.add(new THREE.DirectionalLight(0xffffff, 1.2));
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));

    new THREE.GLTFExporter().parse(
      scene,
      glb => resolve(URL.createObjectURL(new Blob([glb], { type: 'model/gltf-binary' }))),
      reject,
      { binary: true }
    );
  });
}
