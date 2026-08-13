/**
 * LG AR SpaceVision — app.js v4
 * Fix: encode GLB path properly before setting model-viewer src
 * Fix: loading overlay controlled by model-viewer events (not timeout)
 * Fix: wall/floor placement + scan instructions
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

// ─── Load products.json ──────────────────────────
async function loadProducts() {
  try {
    const r = await fetch('products.json');
    state.products = await r.json();
    state.filteredProducts = [...state.products];
    renderProducts();
  } catch (e) {
    console.error('products.json load failed:', e);
  }
}

// ─── Render cards ────────────────────────────────
function renderProducts() {
  const grid = $('productsGrid');
  grid.innerHTML = '';

  if (!state.filteredProducts.length) {
    grid.innerHTML = `<div class="empty-state"><i class="bi bi-inbox"></i><p>Không tìm thấy sản phẩm.</p></div>`;
    return;
  }

  state.filteredProducts.forEach(prod => {
    const card = document.createElement('div');
    card.className = 'product-card';
    const thumb = prod.images?.front || Object.values(prod.images || {}).find(v => v) || null;
    const isWall = prod.placement === 'wall';
    const hasGLB = !!prod.glbFile;
    const sizeMB  = prod.glbSizeMB || null;

    // Thumbnail: use image if available, else colored placeholder
    const thumbHtml = thumb
      ? `<img src="${encodePath(thumb)}" alt="${prod.name}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
         <div class="thumb-placeholder" style="display:none"><i class="bi bi-box-seam"></i></div>`
      : `<div class="thumb-placeholder"><i class="bi bi-${isWall ? 'wind' : 'tornado'}"></i></div>`;

    card.innerHTML = `
      <div class="card-thumb">
        <span class="card-placement-badge ${isWall ? 'wall' : ''}">
          <i class="bi bi-${isWall ? 'layout-wtf' : 'grid'}"></i>
          ${isWall ? 'Treo tường' : 'Đặt sàn'}
        </span>
        ${hasGLB ? `<span class="card-glb-badge"><i class="bi bi-box"></i> 3D ${sizeMB ? `~${sizeMB}MB` : 'GLB'}</span>` : ''}
        ${thumbHtml}
      </div>
      <div class="card-body">
        <div class="card-cat">${prod.category}</div>
        <div class="card-name">${prod.name}</div>
        <div class="card-specs">
          <div class="spec"><span class="spec-label">Cao</span><span class="spec-val">${prod.dimensions?.height ?? '?'}</span></div>
          <div class="spec"><span class="spec-label">Ngang</span><span class="spec-val">${prod.dimensions?.width ?? '?'}</span></div>
          <div class="spec"><span class="spec-label">Sâu</span><span class="spec-val">${prod.dimensions?.depth ?? '?'}</span></div>
        </div>
        <div class="card-actions">
          <button class="btn-ar btn-ar-launch">
            <i class="bi bi-camera-fill"></i> Thử AR Trong Phòng
          </button>
          <button class="btn-3d btn-3d-view">
            <i class="bi bi-box-seam"></i> Xem 3D 360°
          </button>
        </div>
      </div>`;

    // Critical fix: attach events directly in closure (avoids selector bugs)
    card.querySelector('.btn-ar-launch').addEventListener('click', e => {
      e.stopPropagation();
      openViewer(prod);
    });
    card.querySelector('.btn-3d-view').addEventListener('click', e => {
      e.stopPropagation();
      openViewer(prod);
    });

    grid.appendChild(card);
  });
}

// ─── Path encoder (handles Vietnamese chars + spaces) ───
function encodePath(path) {
  if (!path) return '';
  // Encode each segment individually, preserve slashes
  return path.split('/').map(seg => encodeURIComponent(seg)).join('/');
}

// ─── Open viewer modal ───────────────────────────
async function openViewer(product) {
  state.selectedProduct = product;
  const mv = $('modelViewer');
  const isWall = product.placement === 'wall';

  // Update header
  $('arModalTitle').textContent = product.name;
  $('scaleBadge').innerHTML = `
    <i class="bi bi-rulers"></i>
    ${product.dimensions?.height}H × ${product.dimensions?.width}W × ${product.dimensions?.depth}D cm`;

  // Placement instruction
  const tip = $('scanTip');
  tip.className = `scan-tip ${isWall ? 'wall' : 'floor'}`;
  $('scanTipText').innerHTML = isWall
    ? `<strong>Máy lạnh treo tường</strong> — Hướng camera vào <strong>TƯỜNG</strong>, di chuyển chậm để quét, rồi bấm <strong>Bật AR</strong>`
    : `Hướng camera xuống <strong>SÀN nhà</strong>, di chuyển chậm để quét, rồi bấm <strong>Bật AR</strong>`;

  // AR placement
  mv.setAttribute('ar-placement', isWall ? 'wall' : 'floor');

  // WALL ORIENTATION FIX:
  // GLBs are modelled with Y=up (floor placement). With ar-placement="wall",
  // model-viewer makes local-Y perpendicular to wall — so the AC's height
  // sticks OUT from wall instead of standing upright.
  // Fix: pre-rotate -90° around X so the model's depth (Z) becomes wall-normal (Y).
  if (isWall) {
    mv.setAttribute('orientation', '-90deg 0deg 0deg');
  } else {
    mv.removeAttribute('orientation');
  }

  // Show modal + loading
  $('arModal').classList.add('active');
  showLoading(true, product.glbSizeMB);

  // CRITICAL FIX: properly encode path with Vietnamese chars/spaces
  mv.removeAttribute('src');
  if (product.glbFile) {
    mv.setAttribute('src', encodePath(product.glbFile));
  } else {
    try {
      const url = await generateFallbackGLB(product);
      mv.setAttribute('src', url);
    } catch (err) {
      console.error('Fallback GLB error:', err);
      showLoading(false);
    }
  }
}

// ─── model-viewer events ─────────────────────────
function setupModelViewerEvents() {
  const mv = $('modelViewer');

  // Hide loading when model is ready
  mv.addEventListener('load', () => {
    showLoading(false);
    const arBtn = $('arBtn');
    if (!mv.canActivateAR) {
      if (arBtn) arBtn.style.display = 'none';
      $('arUnavail').style.display = 'flex';
    } else {
      if (arBtn) arBtn.style.display = 'flex';
      $('arUnavail').style.display = 'none';
    }
  });

  // If model errors (wrong path, CORS, etc.)
  mv.addEventListener('error', e => {
    console.error('model-viewer error:', e);
    showLoading(false);
    $('arUnavail').style.display = 'flex';
    $('arUnavail').innerHTML = `<i class="bi bi-exclamation-triangle"></i> Không tải được mô hình 3D. File GLB có thể đang bị lỗi đường dẫn.`;
  });

  // AR session feedback
  mv.addEventListener('ar-status', e => {
    const arBtn = $('arBtn');
    if (e.detail.status === 'session-started') {
      if (arBtn) arBtn.innerHTML = `<i class="bi bi-record-circle-fill"></i> AR đang chạy...`;
    } else if (e.detail.status === 'not-presenting') {
      if (arBtn) arBtn.innerHTML = `<i class="bi bi-camera-fill"></i> Bật AR — Đặt vào phòng`;
    } else if (e.detail.status === 'failed') {
      alert('AR không khởi động được.\n\n• Cấp quyền Camera cho trình duyệt\n• Dùng Safari iOS 15+ hoặc Chrome Android\n• Truy cập qua HTTPS (link Cloudflare đang dùng ✓)');
      if (arBtn) arBtn.innerHTML = `<i class="bi bi-camera-fill"></i> Bật AR — Đặt vào phòng`;
    }
  });
}

function showLoading(show, sizeMB = null) {
  const el = $('mvLoading');
  el.style.display = show ? 'flex' : 'none';
  if (show && sizeMB) {
    el.innerHTML = `
      <div class="mv-spinner"></div>
      <span>Đang tải mô hình 3D...</span>
      <span class="load-size-warn"><i class="bi bi-exclamation-triangle-fill"></i> File nặng ~${sizeMB}MB — cần WiFi, có thể mất 30-60 giây</span>`;
  } else if (show) {
    el.innerHTML = `<div class="mv-spinner"></div><span>Đang tải mô hình 3D...</span>`;
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
  // AR modal
  $('arModalClose').addEventListener('click', closeARModal);
  $('arModal').addEventListener('click', e => {
    if (e.target === $('arModal')) closeARModal();
  });

  // Upload modal
  $('btnOpenUpload').addEventListener('click', () => $('uploadModal').classList.add('active'));
  $('uploadModalClose').addEventListener('click', () => $('uploadModal').classList.remove('active'));
  $('uploadModal').addEventListener('click', e => {
    if (e.target === $('uploadModal')) $('uploadModal').classList.remove('active');
  });

  // Form submit
  $('addProductForm').addEventListener('submit', handleAddProduct);
}

function closeARModal() {
  $('arModal').classList.remove('active');
  const mv = $('modelViewer');
  mv.removeAttribute('src');
  mv.removeAttribute('ar-placement');
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
  const frontUrl  = frontFile ? URL.createObjectURL(frontFile) : 'product info/Tủ lạnh/front_processed.png';

  const catMap = {
    'Tủ lạnh': 'refrigerator', 'Máy giặt': 'washer',
    'TV OLED': 'tv', 'Máy lạnh': 'ac', 'Máy lọc KK': 'purifier'
  };

  const prod = {
    id: `custom-${Date.now()}`,
    name, category,
    categoryKey: catMap[category] || 'other',
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

// ─── Fallback box GLB (no .glb file, uses Three.js export) ──
function makeMat(tex) {
  return tex
    ? new THREE.MeshStandardMaterial({ map: tex, transparent: true, alphaTest: .1, metalness: .2, roughness: .3 })
    : new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: .5, roughness: .3 });
}

async function generateFallbackGLB(product) {
  if (typeof THREE === 'undefined' || !THREE.GLTFExporter) throw new Error('Three.js not ready');

  return new Promise((resolve, reject) => {
    const W = (product.dimensions?.width  || 60) / 100;
    const H = (product.dimensions?.height || 100) / 100;
    const D = (product.dimensions?.depth  || 50) / 100;

    const loader = new THREE.TextureLoader();
    const imgs = product.images || {};
    const load = p => p ? loader.load(encodePath(p)) : null;

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
    scene.add(new THREE.AmbientLight(0xffffff, .8));

    new THREE.GLTFExporter().parse(
      scene,
      glb => resolve(URL.createObjectURL(new Blob([glb], { type: 'model/gltf-binary' }))),
      reject,
      { binary: true }
    );
  });
}
