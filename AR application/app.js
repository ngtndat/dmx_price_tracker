/**
 * AR Product Viewer Engine
 * Instant User Gesture iOS Safari Camera Stream & 3D Interactive WebAR.
 */

// Application State
const state = {
  products: [],
  filteredProducts: [],
  activeCategory: 'all',
  selectedProduct: null,
  glbCache: new Map(),
  
  // Live Camera WebAR state
  cameraStream: null,
  threeScene: null,
  threeCamera: null,
  threeRenderer: null,
  productMesh: null,
  animFrameId: null,
  isCameraOpening: false,
  touchState: {
    isDragging: false,
    lastX: 0,
    lastY: 0,
    posX: 0,
    posY: 0,
    rotationY: 0
  }
};

// DOM Elements
const elements = {
  productsGrid: document.getElementById('productsGrid'),
  categoryChips: document.querySelectorAll('.category-chip'),
  arModal: document.getElementById('arModal'),
  arModalTitle: document.getElementById('arModalTitle'),
  arModalClose: document.getElementById('arModalClose'),
  modelViewer: document.getElementById('modelViewer'),
  scaleBadge: document.getElementById('scaleBadge'),
  uploadModal: document.getElementById('uploadModal'),
  btnOpenUpload: document.getElementById('btnOpenUpload'),
  uploadModalClose: document.getElementById('uploadModalClose'),
  addProductForm: document.getElementById('addProductForm'),
  
  // Live Camera WebAR Elements
  btnModalLaunchCamera: document.getElementById('btnModalLaunchCamera'),
  liveCameraModal: document.getElementById('liveCameraModal'),
  btnCloseLiveCamera: document.getElementById('btnCloseLiveCamera'),
  cameraVideo: document.getElementById('cameraVideo'),
  cameraCanvas: document.getElementById('cameraCanvas'),
  liveCameraTitle: document.getElementById('liveCameraTitle'),
  btnCapturePhoto: document.getElementById('btnCapturePhoto')
};

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  await loadProducts();
  setupEventListeners();
});

// Load products from JSON
async function loadProducts() {
  try {
    const res = await fetch('products.json');
    state.products = await res.json();
    state.filteredProducts = [...state.products];
    renderProducts();
  } catch (err) {
    console.error('Failed to load products.json:', err);
  }
}

// Render product cards with touch-friendly action buttons
function renderProducts() {
  elements.productsGrid.innerHTML = '';

  if (state.filteredProducts.length === 0) {
    elements.productsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">
        <i class="ri-inbox-line" style="font-size: 3rem;"></i>
        <p style="margin-top: 1rem;">Không tìm thấy sản phẩm phù hợp.</p>
      </div>
    `;
    return;
  }

  state.filteredProducts.forEach(prod => {
    const card = document.createElement('div');
    card.className = 'product-card';

    const thumbImage = prod.images.front || Object.values(prod.images)[0];
    const placementClass = prod.placement === 'wall' ? 'wall' : 'floor';
    const placementText = prod.placement === 'wall' ? 'Treo tường (Wall)' : 'Đặt sàn (Floor)';

    card.innerHTML = `
      <div class="product-thumb-container">
        <span class="placement-badge ${placementClass}">
          <i class="${prod.placement === 'wall' ? 'ri-layout-3-line' : 'ri-grid-line'}"></i> ${placementText}
        </span>
        <img src="${encodeURI(thumbImage)}" alt="${prod.name}" class="product-thumb-img" loading="lazy" />
      </div>
      <div class="product-info">
        <span class="product-category">${prod.category}</span>
        <h3 class="product-title">${prod.name}</h3>
        
        <div class="product-specs">
          <div class="spec-item">
            <span class="spec-label">Cao</span>
            <span class="spec-val">${prod.dimensions.height} cm</span>
          </div>
          <div class="spec-item">
            <span class="spec-label">Ngang</span>
            <span class="spec-val">${prod.dimensions.width} cm</span>
          </div>
          <div class="spec-item">
            <span class="spec-label">Sâu</span>
            <span class="spec-val">${prod.dimensions.depth} cm</span>
          </div>
        </div>

        <div class="product-actions">
          <button type="button" class="btn btn-primary btn-ar-direct" data-id="${prod.id}">
            <i class="ri-camera-fill"></i> Bật Camera AR Trong Phòng
          </button>
          <button type="button" class="btn btn-glass btn-3d-view" data-id="${prod.id}">
            <i class="ri-box-3-line"></i> Xem 3D 360°
          </button>
        </div>
      </div>
    `;

    // Direct Camera Button Handler (instant touch trigger for iOS Safari)
    const btnDirectCamera = card.querySelector('.btn-ar-direct');
    
    const triggerCamera = () => {
      if (state.isCameraOpening) return;
      state.isCameraOpening = true;
      requestCameraAndOpenModal(prod);
      setTimeout(() => { state.isCameraOpening = false; }, 1000);
    };

    btnDirectCamera.addEventListener('click', triggerCamera);

    // 3D View Button Handler
    const btn3DView = card.querySelector('.btn-3d-view');
    btn3DView.addEventListener('click', () => openARViewer(prod));

    elements.productsGrid.appendChild(card);
  });
}

// Request Camera Stream synchronously in user click gesture context
function requestCameraAndOpenModal(product) {
  if (!product) return;
  state.selectedProduct = product;

  // Check getUserMedia support
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('Trình duyệt của bạn không hỗ trợ camera. Vui lòng thử lại trên trình duyệt Safari (iOS) hoặc Chrome (Android).');
    return;
  }

  // Request camera IMMEDIATELY in user gesture call stack
  navigator.mediaDevices.getUserMedia({
    video: { facingMode: { ideal: 'environment' } },
    audio: false
  })
  .then(stream => {
    state.cameraStream = stream;
    elements.cameraVideo.srcObject = stream;
    elements.cameraVideo.setAttribute('playsinline', 'true');
    elements.cameraVideo.setAttribute('webkit-playsinline', 'true');
    elements.cameraVideo.play();

    // Show modal and start 3D canvas
    elements.liveCameraTitle.textContent = `Camera WebAR - ${product.name}`;
    elements.liveCameraModal.classList.add('active');

    state.touchState.posX = 0;
    state.touchState.posY = -0.2;
    state.touchState.rotationY = 0;

    initThreeJSCameraCanvas(product);
  })
  .catch(err => {
    console.error('Camera permission error:', err);
    alert('Vui lòng cấp quyền mở Camera trong cài đặt Safari/Chrome trên điện thoại:\n\n1. Bấm vào biểu tượng Cài đặt / Quyền riêng tư ở thanh địa chỉ.\n2. Chọn Camera -> Cho phép (Allow).\n3. Tải lại trang và thử lại!');
  });
}

// Setup Event Listeners
function setupEventListeners() {
  // Category Chips Filter
  elements.categoryChips.forEach(chip => {
    chip.addEventListener('click', () => {
      elements.categoryChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const cat = chip.dataset.category;
      state.activeCategory = cat;

      if (cat === 'all') {
        state.filteredProducts = [...state.products];
      } else {
        state.filteredProducts = state.products.filter(p => p.categoryKey === cat);
      }
      renderProducts();
    });
  });

  // Modal Closers
  elements.arModalClose.addEventListener('click', closeARModal);
  elements.uploadModalClose.addEventListener('click', closeUploadModal);
  elements.btnOpenUpload.addEventListener('click', openUploadModal);

  // Close modals on background overlay click
  elements.arModal.addEventListener('click', e => {
    if (e.target === elements.arModal) closeARModal();
  });
  elements.uploadModal.addEventListener('click', e => {
    if (e.target === elements.uploadModal) closeUploadModal();
  });

  // Add Product Form Submission
  elements.addProductForm.addEventListener('submit', handleAddProductSubmit);

  // Modal Launch Camera Button
  if (elements.btnModalLaunchCamera) {
    elements.btnModalLaunchCamera.addEventListener('click', () => {
      closeARModal();
      if (state.selectedProduct) {
        requestCameraAndOpenModal(state.selectedProduct);
      }
    });
  }

  // Live Camera WebAR closers and photo capture
  elements.btnCloseLiveCamera.addEventListener('click', closeLiveCameraModal);
  elements.btnCapturePhoto.addEventListener('click', capturePhoto);

  // Touch gesture listeners on camera canvas
  setupCanvasTouchGestures();
}

// Create Three.js Material with transparent PNG textures and solid appliance background
function createProductMaterial(texture, baseColor = 0xffffff) {
  if (!texture) {
    return new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.5,
      roughness: 0.3
    });
  }
  return new THREE.MeshStandardMaterial({
    map: texture,
    transparent: true,
    alphaTest: 0.1,
    color: baseColor,
    metalness: 0.2,
    roughness: 0.3
  });
}

// Generate 1:1 Scale Procedural 3D Model with Multi-Angle Textures
async function generate3DModel(product) {
  if (state.glbCache.has(product.id)) {
    return state.glbCache.get(product.id);
  }

  return new Promise((resolve, reject) => {
    const W = product.dimensions.width / 100;
    const H = product.dimensions.height / 100;
    const D = product.dimensions.depth / 100;

    const geometry = new THREE.BoxGeometry(W, H, D);
    const textureLoader = new THREE.TextureLoader();

    const imgs = product.images;
    const frontTex = imgs.front ? textureLoader.load(encodeURI(imgs.front)) : null;
    const backTex = imgs.back ? textureLoader.load(encodeURI(imgs.back)) : null;
    const leftTex = imgs.left ? textureLoader.load(encodeURI(imgs.left)) : null;
    const rightTex = imgs.right ? textureLoader.load(encodeURI(imgs.right)) : null;
    const topTex = imgs.top ? textureLoader.load(encodeURI(imgs.top)) : null;

    const materials = [
      createProductMaterial(rightTex), // Right (+X)
      createProductMaterial(leftTex),  // Left (-X)
      createProductMaterial(topTex),   // Top (+Y)
      createProductMaterial(null),     // Bottom (-Y)
      createProductMaterial(frontTex), // Front (+Z)
      createProductMaterial(backTex)   // Back (-Z)
    ];

    const mesh = new THREE.Mesh(geometry, materials);
    mesh.position.set(0, H / 2, 0);

    const scene = new THREE.Scene();
    scene.add(mesh);

    const light = new THREE.DirectionalLight(0xffffff, 1.2);
    light.position.set(2, 4, 3);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));

    const exporter = new THREE.GLTFExporter();
    exporter.parse(
      scene,
      function (gltf) {
        const blob = new Blob([gltf], { type: 'model/gltf-binary' });
        const blobUrl = URL.createObjectURL(blob);
        state.glbCache.set(product.id, blobUrl);
        resolve(blobUrl);
      },
      function (error) {
        console.error('Error generating GLB model:', error);
        reject(error);
      },
      { binary: true }
    );
  });
}

// Open AR Viewport Modal
async function openARViewer(product) {
  state.selectedProduct = product;
  elements.arModalTitle.textContent = `${product.name} (Tỉ lệ thực 1:1)`;
  elements.scaleBadge.innerHTML = `<i class="ri-ruler-line"></i> ${product.dimensions.height}H × ${product.dimensions.width}W × ${product.dimensions.depth}D cm`;

  elements.arModal.classList.add('active');

  try {
    const glbUrl = await generate3DModel(product);
    elements.modelViewer.setAttribute('src', glbUrl);
  } catch (err) {
    console.error('Could not generate 3D model:', err);
  }
}

// Close AR Modal
function closeARModal() {
  elements.arModal.classList.remove('active');
  elements.modelViewer.removeAttribute('src');
}

// -------------------------------------------------------------
// Three.js Overlaid 3D Canvas Engine
// -------------------------------------------------------------
function initThreeJSCameraCanvas(product) {
  const width = window.innerWidth;
  const height = window.innerHeight;

  state.threeScene = new THREE.Scene();
  state.threeCamera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
  state.threeCamera.position.set(0, 1.2, 2.5);
  state.threeCamera.lookAt(0, 0, 0);

  state.threeRenderer = new THREE.WebGLRenderer({
    canvas: elements.cameraCanvas,
    alpha: true,
    antialias: true
  });
  state.threeRenderer.setSize(width, height);
  state.threeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const light = new THREE.DirectionalLight(0xffffff, 1.4);
  light.position.set(3, 5, 4);
  state.threeScene.add(light);
  state.threeScene.add(new THREE.AmbientLight(0xffffff, 0.9));

  const W = product.dimensions.width / 100;
  const H = product.dimensions.height / 100;
  const D = product.dimensions.depth / 100;

  // Solid Inner Chassis Box (Realistic Metallic Body)
  const chassisGeom = new THREE.BoxGeometry(W * 0.99, H * 0.99, D * 0.99);
  const chassisMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b,
    metalness: 0.6,
    roughness: 0.2
  });
  const chassisMesh = new THREE.Mesh(chassisGeom, chassisMat);

  // Outer Textured Box with Transparent Processed PNGs
  const geometry = new THREE.BoxGeometry(W, H, D);
  const textureLoader = new THREE.TextureLoader();

  const imgs = product.images;
  const frontTex = imgs.front ? textureLoader.load(encodeURI(imgs.front)) : null;
  const backTex = imgs.back ? textureLoader.load(encodeURI(imgs.back)) : null;
  const leftTex = imgs.left ? textureLoader.load(encodeURI(imgs.left)) : null;
  const rightTex = imgs.right ? textureLoader.load(encodeURI(imgs.right)) : null;
  const topTex = imgs.top ? textureLoader.load(encodeURI(imgs.top)) : null;

  const materials = [
    createProductMaterial(rightTex), // Right (+X)
    createProductMaterial(leftTex),  // Left (-X)
    createProductMaterial(topTex),   // Top (+Y)
    createProductMaterial(null),     // Bottom (-Y)
    createProductMaterial(frontTex), // Front (+Z)
    createProductMaterial(backTex)   // Back (-Z)
  ];

  const outerMesh = new THREE.Mesh(geometry, materials);

  // Group inner chassis + outer textured mesh
  state.productMesh = new THREE.Group();
  state.productMesh.add(chassisMesh);
  state.productMesh.add(outerMesh);

  state.productMesh.position.set(0, -0.2, 0);
  state.threeScene.add(state.productMesh);

  function animate() {
    if (!elements.liveCameraModal.classList.contains('active')) return;
    state.animFrameId = requestAnimationFrame(animate);

    if (state.productMesh) {
      state.productMesh.rotation.y = state.touchState.rotationY;
      state.productMesh.position.x = state.touchState.posX;
      state.productMesh.position.y = state.touchState.posY;
    }

    state.threeRenderer.render(state.threeScene, state.threeCamera);
  }
  animate();
}

// Touch Gestures for Moving and Rotating 3D Product over Live Camera
function setupCanvasTouchGestures() {
  const canvas = elements.cameraCanvas;

  canvas.addEventListener('touchstart', e => {
    if (e.touches.length === 1) {
      state.touchState.isDragging = true;
      state.touchState.lastX = e.touches[0].clientX;
      state.touchState.lastY = e.touches[0].clientY;
    }
  }, { passive: true });

  canvas.addEventListener('touchmove', e => {
    if (!state.touchState.isDragging || e.touches.length !== 1) return;

    const deltaX = e.touches[0].clientX - state.touchState.lastX;
    const deltaY = e.touches[0].clientY - state.touchState.lastY;

    state.touchState.rotationY += deltaX * 0.01;
    state.touchState.posY -= deltaY * 0.003;

    state.touchState.lastX = e.touches[0].clientX;
    state.touchState.lastY = e.touches[0].clientY;
  }, { passive: true });

  canvas.addEventListener('touchend', () => {
    state.touchState.isDragging = false;
  });
}

// Close Live Camera Modal
function closeLiveCameraModal() {
  elements.liveCameraModal.classList.remove('active');
  if (state.animFrameId) {
    cancelAnimationFrame(state.animFrameId);
    state.animFrameId = null;
  }
  if (state.cameraStream) {
    state.cameraStream.getTracks().forEach(track => track.stop());
    state.cameraStream = null;
  }
}

// Capture Photo inside Camera Room View
function capturePhoto() {
  const canvas = document.createElement('canvas');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const ctx = canvas.getContext('2d');

  ctx.drawImage(elements.cameraVideo, 0, 0, canvas.width, canvas.height);
  ctx.drawImage(elements.cameraCanvas, 0, 0, canvas.width, canvas.height);

  const link = document.createElement('a');
  link.download = `AR_Product_${Date.now()}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

// Open / Close Upload Modal
function openUploadModal() {
  elements.uploadModal.classList.add('active');
}

function closeUploadModal() {
  elements.uploadModal.classList.remove('active');
}

// Handle Add Product Submit
function handleAddProductSubmit(e) {
  e.preventDefault();
  const form = elements.addProductForm;

  const name = form.prodName.value.trim();
  const category = form.prodCategory.value;
  const height = parseFloat(form.prodHeight.value);
  const width = parseFloat(form.prodWidth.value);
  const depth = parseFloat(form.prodDepth.value);
  const placement = form.prodPlacement.value;

  if (!name || !height || !width || !depth) {
    alert('Vui lòng nhập đầy đủ tên và kích thước (Cao, Ngang, Sâu)!');
    return;
  }

  const frontFile = form.imgFront.files[0];
  const frontUrl = frontFile ? URL.createObjectURL(frontFile) : 'product info/Tủ lạnh/front_processed.png';
  const leftFile = form.imgLeft.files[0];
  const leftUrl = leftFile ? URL.createObjectURL(leftFile) : frontUrl;
  const rightFile = form.imgRight.files[0];
  const rightUrl = rightFile ? URL.createObjectURL(rightFile) : frontUrl;
  const backFile = form.imgBack.files[0];
  const backUrl = backFile ? URL.createObjectURL(backFile) : frontUrl;

  const categoryMap = {
    'Tủ lạnh': 'refrigerator',
    'Máy giặt': 'washer',
    'TV OLED': 'tv',
    'Máy lạnh': 'ac'
  };

  const newProduct = {
    id: `custom-${Date.now()}`,
    name,
    category,
    categoryKey: categoryMap[category] || 'other',
    placement,
    dimensions: { height, width, depth, unit: 'cm' },
    images: {
      front: frontUrl,
      left: leftUrl,
      right: rightUrl,
      back: backUrl
    },
    description: 'Sản phẩm tạo mới từ bảng quản trị.'
  };

  state.products.unshift(newProduct);
  state.filteredProducts = [...state.products];
  renderProducts();

  closeUploadModal();
  form.reset();

  requestCameraAndOpenModal(newProduct);
}
