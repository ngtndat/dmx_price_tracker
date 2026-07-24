/**
 * AR Product Viewer Engine
 * Dual-Mode WebAR: Direct Camera Feed Overlay & 3D Interactive Viewer.
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

// Render product cards with direct action buttons
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
          <button class="btn btn-primary btn-ar-direct" data-id="${prod.id}">
            <i class="ri-camera-fill"></i> Bật Camera AR Trong Phòng
          </button>
          <button class="btn btn-glass btn-3d-view" data-id="${prod.id}">
            <i class="ri-box-3-line"></i> Xem 3D 360°
          </button>
        </div>
      </div>
    `;

    // Direct Camera Button Handler
    const btnDirectCamera = card.querySelector('.btn-ar-direct');
    btnDirectCamera.addEventListener('click', (e) => {
      e.stopPropagation();
      openLiveCameraModal(prod);
    });

    // 3D View Button Handler
    const btn3DView = card.querySelector('.btn-3d-view');
    btn3DView.addEventListener('click', (e) => {
      e.stopPropagation();
      openARViewer(prod);
    });

    elements.productsGrid.appendChild(card);
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
        openLiveCameraModal(state.selectedProduct);
      }
    });
  }

  // Live Camera WebAR closers and photo capture
  elements.btnCloseLiveCamera.addEventListener('click', closeLiveCameraModal);
  elements.btnCapturePhoto.addEventListener('click', capturePhoto);

  // Touch gesture listeners on camera canvas
  setupCanvasTouchGestures();
}

// Generate 1:1 Scale Procedural 3D Model with Multi-Angle Textures
async function generate3DModel(product) {
  if (state.glbCache.has(product.id)) {
    return state.glbCache.get(product.id);
  }

  return new Promise((resolve, reject) => {
    const W = product.dimensions.width / 100;  // convert cm to meters
    const H = product.dimensions.height / 100;
    const D = product.dimensions.depth / 100;

    const geometry = new THREE.BoxGeometry(W, H, D);
    const textureLoader = new THREE.TextureLoader();

    const imgs = product.images;
    const frontTex = imgs.front ? textureLoader.load(imgs.front) : null;
    const backTex = imgs.back ? textureLoader.load(imgs.back) : frontTex;
    const leftTex = imgs.left ? textureLoader.load(imgs.left) : frontTex;
    const rightTex = imgs.right ? textureLoader.load(imgs.right) : frontTex;
    const topTex = imgs.top ? textureLoader.load(imgs.top) : frontTex;

    const defaultMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.3 });

    const materials = [
      rightTex ? new THREE.MeshStandardMaterial({ map: rightTex, roughness: 0.4 }) : defaultMat,
      leftTex ? new THREE.MeshStandardMaterial({ map: leftTex, roughness: 0.4 }) : defaultMat,
      topTex ? new THREE.MeshStandardMaterial({ map: topTex, roughness: 0.4 }) : defaultMat,
      defaultMat,
      frontTex ? new THREE.MeshStandardMaterial({ map: frontTex, roughness: 0.3 }) : defaultMat,
      backTex ? new THREE.MeshStandardMaterial({ map: backTex, roughness: 0.4 }) : defaultMat
    ];

    const mesh = new THREE.Mesh(geometry, materials);
    mesh.position.set(0, H / 2, 0); // Base at Y=0

    const scene = new THREE.Scene();
    scene.add(mesh);

    // Lights
    const light = new THREE.DirectionalLight(0xffffff, 1.2);
    light.position.set(2, 4, 3);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));

    // Export scene to GLB Blob
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

  // Show Modal Overlay
  elements.arModal.classList.add('active');

  // Generate 3D Model dynamically
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
// Live Web Camera WebAR Engine (Direct Touch & iOS Safari Friendly)
// -------------------------------------------------------------
async function openLiveCameraModal(product) {
  if (!product) return;
  state.selectedProduct = product;

  elements.liveCameraTitle.textContent = `Camera WebAR - ${product.name}`;
  elements.liveCameraModal.classList.add('active');

  // Reset touch state
  state.touchState.posX = 0;
  state.touchState.posY = -0.2;
  state.touchState.rotationY = 0;

  // 1. Request Camera Feed with iOS Safari Fallback Handling
  try {
    const constraints = [
      { video: { facingMode: { exact: 'environment' } }, audio: false },
      { video: { facingMode: 'environment' }, audio: false },
      { video: true, audio: false }
    ];

    let stream = null;
    for (const constraint of constraints) {
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraint);
        if (stream) break;
      } catch (err) {
        // try next fallback
      }
    }

    if (stream) {
      state.cameraStream = stream;
      elements.cameraVideo.srcObject = stream;
      elements.cameraVideo.setAttribute('playsinline', 'true');
      elements.cameraVideo.setAttribute('webkit-playsinline', 'true');
      await elements.cameraVideo.play().catch(e => console.log('Auto play bypass:', e));
    } else {
      alert('Không thể mở Camera trên thiết bị. Vui lòng cho phép quyền Camera trong cài đặt trình duyệt!');
    }
  } catch (err) {
    console.error('Camera access error:', err);
  }

  // 2. Initialize Three.js Overlaid 3D Canvas
  initThreeJSCameraCanvas(product);
}

function initThreeJSCameraCanvas(product) {
  const width = window.innerWidth;
  const height = window.innerHeight;

  // Scene, Camera, Renderer
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

  // Lights
  const light = new THREE.DirectionalLight(0xffffff, 1.2);
  light.position.set(3, 5, 4);
  state.threeScene.add(light);
  state.threeScene.add(new THREE.AmbientLight(0xffffff, 0.8));

  // Construct 1:1 scale cuboid mesh
  const W = product.dimensions.width / 100;
  const H = product.dimensions.height / 100;
  const D = product.dimensions.depth / 100;

  const geometry = new THREE.BoxGeometry(W, H, D);
  const textureLoader = new THREE.TextureLoader();

  const imgs = product.images;
  const frontTex = imgs.front ? textureLoader.load(imgs.front) : null;
  const backTex = imgs.back ? textureLoader.load(imgs.back) : frontTex;
  const leftTex = imgs.left ? textureLoader.load(imgs.left) : frontTex;
  const rightTex = imgs.right ? textureLoader.load(imgs.right) : frontTex;
  const topTex = imgs.top ? textureLoader.load(imgs.top) : frontTex;

  const defaultMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.3 });

  const materials = [
    rightTex ? new THREE.MeshStandardMaterial({ map: rightTex, roughness: 0.4 }) : defaultMat,
    leftTex ? new THREE.MeshStandardMaterial({ map: leftTex, roughness: 0.4 }) : defaultMat,
    topTex ? new THREE.MeshStandardMaterial({ map: topTex, roughness: 0.4 }) : defaultMat,
    defaultMat,
    frontTex ? new THREE.MeshStandardMaterial({ map: frontTex, roughness: 0.3 }) : defaultMat,
    backTex ? new THREE.MeshStandardMaterial({ map: backTex, roughness: 0.4 }) : defaultMat
  ];

  state.productMesh = new THREE.Mesh(geometry, materials);
  state.productMesh.position.set(0, -0.2, 0);
  state.threeScene.add(state.productMesh);

  // Render loop
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

  // Touch start
  canvas.addEventListener('touchstart', e => {
    if (e.touches.length === 1) {
      state.touchState.isDragging = true;
      state.touchState.lastX = e.touches[0].clientX;
      state.touchState.lastY = e.touches[0].clientY;
    }
  }, { passive: true });

  // Touch move
  canvas.addEventListener('touchmove', e => {
    if (!state.touchState.isDragging || e.touches.length !== 1) return;

    const deltaX = e.touches[0].clientX - state.touchState.lastX;
    const deltaY = e.touches[0].clientY - state.touchState.lastY;

    state.touchState.rotationY += deltaX * 0.01;
    state.touchState.posY -= deltaY * 0.003;

    state.touchState.lastX = e.touches[0].clientX;
    state.touchState.lastY = e.touches[0].clientY;
  }, { passive: true });

  // Touch end
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

  // Draw video background
  ctx.drawImage(elements.cameraVideo, 0, 0, canvas.width, canvas.height);
  // Draw 3D product canvas overlay
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
  const frontUrl = frontFile ? URL.createObjectURL(frontFile) : 'product info/Tủ lạnh/front.jpg';
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

  openLiveCameraModal(newProduct);
}
