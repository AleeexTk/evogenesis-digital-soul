// ===================================
// EVO_PYRAMID 3D Interface
// Three.js Implementation
// ===================================

const CORE_API_URL = '/api/bridge/protocol';

// State
let scene, camera, renderer, controls;
let pyramidGroup, particleSystem;
let protocolData = null;
let autoRotate = true;
let selectedModule = null;

// Module Configuration
const MODULE_CONFIG = {
    'CORE': {
        position: [0, 0, 0],
        color: 0xffffff,
        emissive: 0xffffff,
        label: 'CORE'
    },
    'SOUL': {
        position: [0, 1.5, 0],
        color: 0x00ff9d,
        emissive: 0x00ff9d,
        label: 'SOUL',
        faceIndex: 0
    },
    'TRAILBLAZER': {
        position: [1.3, -0.5, 0.75],
        color: 0xffd700,
        emissive: 0xffd700,
        label: 'TRAILBLAZER',
        faceIndex: 1
    },
    'PROVOCATEUR': {
        position: [-1.3, -0.5, 0.75],
        color: 0xff4d4d,
        emissive: 0xff4d4d,
        label: 'PROVOCATEUR',
        faceIndex: 2
    },
    'PURPLE_TRIANGLE': {
        position: [0, -0.5, -1.5],
        color: 0xa020f0,
        emissive: 0xa020f0,
        label: 'ANALYST',
        faceIndex: 3
    }
};

// Localization
const TRANSLATIONS = {
    'en': {
        'loading': 'INITIALIZING GENESIS PROTOCOL',
        'log.init': '[SYSTEM] Interface initialized',
        'log.protocol': '[SYSTEM] Loading Genesis Protocol...',
        'log.success': '[SUCCESS] Protocol loaded successfully',
        'log.error': '[ERROR] Failed to load protocol: ',
        'log.click': '[INFO] Selected module: ',
        'log.rotate': '[SYSTEM] Auto-rotation ',
        'log.reset': '[SYSTEM] Camera view reset',
        'log.export': '[SYSTEM] Exporting protocol data...'
    },
    'ua': {
        'loading': 'ІНІЦІАЛІЗАЦІЯ ПРОТОКОЛУ GENESIS',
        'log.init': '[СИСТЕМА] Інтерфейс ініціалізовано',
        'log.protocol': '[СИСТЕМА] Завантаження протоколу Genesis...',
        'log.success': '[УСПІХ] Протокол завантажено успішно',
        'log.error': '[ПОМИЛКА] Не вдалося завантажити протокол: ',
        'log.click': '[ІНФО] Обрано модуль: ',
        'log.rotate': '[СИСТЕМА] Авто-обертання ',
        'log.reset': '[СИСТЕМА] Вигляд камери скинуто',
        'log.export': '[СИСТЕМА] Експорт даних протоколу...'
    }
};

let currentLang = 'ua';

// Utility Functions
function log(message, type = 'system') {
    const console = document.getElementById('console');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    console.appendChild(entry);
    console.scrollTop = console.scrollHeight;
}

function tr(key) {
    return TRANSLATIONS[currentLang][key] || key;
}

window.setLanguage = function(lang) {
    currentLang = lang;
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase() === lang);
    });
    log(`Language switched to: ${lang.toUpperCase()}`, 'system');
};

// ===================================
// Three.js Scene Setup
// ===================================

function initThreeJS() {
    const container = document.getElementById('canvas-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x000000, 10, 50);

    // Camera
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 3, 8);
    camera.lookAt(0, 0, 0);

    // Renderer
    renderer = new THREE.WebGLRenderer({ 
        antialias: true, 
        alpha: true 
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x00ff9d, 1, 100);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xffd700, 1, 100);
    pointLight2.position.set(-5, 5, -5);
    scene.add(pointLight2);

    // Mouse Controls
    setupMouseControls();

    // Handle Resize
    window.addEventListener('resize', onWindowResize);
}

function setupMouseControls() {
    const container = renderer.domElement;
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };

    container.addEventListener('mousedown', (e) => {
        isDragging = true;
        autoRotate = false;
        document.getElementById('btn-auto-rotate').classList.remove('active');
    });

    container.addEventListener('mousemove', (e) => {
        if (isDragging && pyramidGroup) {
            const deltaX = e.clientX - previousMousePosition.x;
            const deltaY = e.clientY - previousMousePosition.y;

            pyramidGroup.rotation.y += deltaX * 0.01;
            pyramidGroup.rotation.x += deltaY * 0.01;
        }
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });

    container.addEventListener('mouseup', () => {
        isDragging = false;
    });

    container.addEventListener('wheel', (e) => {
        e.preventDefault();
        camera.position.z += e.deltaY * 0.01;
        camera.position.z = Math.max(4, Math.min(15, camera.position.z));
    });

    // Click detection for modules
    container.addEventListener('click', onMouseClick);
}

function onMouseClick(event) {
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(scene.children, true);

    if (intersects.length > 0) {
        const object = intersects[0].object;
        if (object.userData.module) {
            showModuleInfo(object.userData.module);
            log(tr('log.click') + object.userData.module, 'info');
        }
    }
}

function onWindowResize() {
    const container = document.getElementById('canvas-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

// ===================================
// Pyramid Creation
// ===================================

function createPyramid() {
    pyramidGroup = new THREE.Group();

    // Create Core (center sphere)
    const coreGeometry = new THREE.SphereGeometry(0.3, 32, 32);
    const coreMaterial = new THREE.MeshPhongMaterial({
        color: 0xffffff,
        emissive: 0xffffff,
        emissiveIntensity: 0.5,
        shininess: 100,
        transparent: true,
        opacity: 0.9
    });
    const core = new THREE.Mesh(coreGeometry, coreMaterial);
    core.userData.module = 'CORE';
    pyramidGroup.add(core);

    // Add core glow
    const coreGlow = new THREE.Mesh(
        new THREE.SphereGeometry(0.35, 32, 32),
        new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.2
        })
    );
    core.add(coreGlow);

    // Create Pyramid Faces
    const pyramidHeight = 2;
    const pyramidBase = 2.6;
    
    const pyramidGeometry = new THREE.BufferGeometry();
    const vertices = new Float32Array([
        // Face 1 (SOUL - top/front)
        0, pyramidHeight, 0,
        -pyramidBase/2, -pyramidHeight/2, pyramidBase/2,
        pyramidBase/2, -pyramidHeight/2, pyramidBase/2,
        
        // Face 2 (TRAILBLAZER - right)
        0, pyramidHeight, 0,
        pyramidBase/2, -pyramidHeight/2, pyramidBase/2,
        pyramidBase/2, -pyramidHeight/2, -pyramidBase/2,
        
        // Face 3 (PROVOCATEUR - left)
        0, pyramidHeight, 0,
        -pyramidBase/2, -pyramidHeight/2, -pyramidBase/2,
        -pyramidBase/2, -pyramidHeight/2, pyramidBase/2,
        
        // Face 4 (PURPLE - back)
        0, pyramidHeight, 0,
        pyramidBase/2, -pyramidHeight/2, -pyramidBase/2,
        -pyramidBase/2, -pyramidHeight/2, -pyramidBase/2,
    ]);

    pyramidGeometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    pyramidGeometry.computeVertexNormals();

    // Create materials for each face
    const faceColors = [
        0x00ff9d, // SOUL
        0xffd700, // TRAILBLAZER
        0xff4d4d, // PROVOCATEUR
        0xa020f0  // PURPLE
    ];

    const moduleNames = ['SOUL', 'TRAILBLAZER', 'PROVOCATEUR', 'PURPLE_TRIANGLE'];

    // Create each face separately for click detection
    for (let i = 0; i < 4; i++) {
        const faceGeometry = new THREE.BufferGeometry();
        const faceVertices = new Float32Array([
            vertices[i * 9], vertices[i * 9 + 1], vertices[i * 9 + 2],
            vertices[i * 9 + 3], vertices[i * 9 + 4], vertices[i * 9 + 5],
            vertices[i * 9 + 6], vertices[i * 9 + 7], vertices[i * 9 + 8]
        ]);
        faceGeometry.setAttribute('position', new THREE.BufferAttribute(faceVertices, 3));
        faceGeometry.computeVertexNormals();

        const faceMaterial = new THREE.MeshPhongMaterial({
            color: faceColors[i],
            emissive: faceColors[i],
            emissiveIntensity: 0.3,
            transparent: true,
            opacity: 0.7,
            side: THREE.DoubleSide,
            shininess: 100
        });

        const face = new THREE.Mesh(faceGeometry, faceMaterial);
        face.userData.module = moduleNames[i];
        pyramidGroup.add(face);
    }

    // Add wireframe
    const wireframeGeometry = new THREE.EdgesGeometry(pyramidGeometry);
    const wireframeMaterial = new THREE.LineBasicMaterial({ 
        color: 0xffffff, 
        transparent: true, 
        opacity: 0.3 
    });
    const wireframe = new THREE.LineSegments(wireframeGeometry, wireframeMaterial);
    pyramidGroup.add(wireframe);

    // Add labels
    createLabels();

    scene.add(pyramidGroup);
}

function createLabels() {
    // Create text sprites for each module
    Object.keys(MODULE_CONFIG).forEach(moduleName => {
        const config = MODULE_CONFIG[moduleName];
        if (config.position) {
            createTextSprite(config.label, config.position, config.color);
        }
    });
}

function createTextSprite(text, position, color) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 256;
    canvas.height = 64;

    context.font = 'Bold 24px Share Tech Mono';
    context.fillStyle = `#${color.toString(16).padStart(6, '0')}`;
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(text, 128, 32);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMaterial = new THREE.SpriteMaterial({ 
        map: texture,
        transparent: true
    });
    const sprite = new THREE.Sprite(spriteMaterial);
    
    sprite.position.set(position[0], position[1] + 0.3, position[2]);
    sprite.scale.set(1, 0.25, 1);
    
    pyramidGroup.add(sprite);
}

// ===================================
// Particle System
// ===================================

function createParticles() {
    const particleCount = 1000;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        
        // Random position in sphere
        const radius = 5 + Math.random() * 5;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.random() * Math.PI;
        
        positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i3 + 2] = radius * Math.cos(phi);

        // Random color (tinted towards pyramid colors)
        const colorChoice = Math.random();
        if (colorChoice < 0.25) {
            colors[i3] = 0; colors[i3 + 1] = 1; colors[i3 + 2] = 0.6; // Soul
        } else if (colorChoice < 0.5) {
            colors[i3] = 1; colors[i3 + 1] = 0.84; colors[i3 + 2] = 0; // Trailblazer
        } else if (colorChoice < 0.75) {
            colors[i3] = 1; colors[i3 + 1] = 0.3; colors[i3 + 2] = 0.3; // Provocateur
        } else {
            colors[i3] = 0.63; colors[i3 + 1] = 0.13; colors[i3 + 2] = 0.94; // Purple
        }
    }

    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
        size: 0.05,
        vertexColors: true,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
    });

    particleSystem = new THREE.Points(particles, particleMaterial);
    scene.add(particleSystem);
}

// ===================================
// Protocol Loading
// ===================================

async function loadProtocol() {
    log(tr('log.protocol'), 'system');
    
    try {
        // Try to load from API
        const response = await fetch(CORE_API_URL);
        if (!response.ok) throw new Error('API not available');
        
        protocolData = await response.json();
        log(tr('log.success'), 'success');
        
    } catch (error) {
        // Fallback to default data
        log(tr('log.error') + 'Using default protocol', 'warn');
        protocolData = getDefaultProtocol();
    }
    
    updateProtocolDisplay();
}

function getDefaultProtocol() {
    return {
        "genesis_meta": {
            "protocol_id": "EVO-GENESIS-V1",
            "timestamp": new Date().toISOString(),
            "version": "1.3.0",
            "state": "ACTIVE"
        },
        "modules": {
            "CORE": {
                "sign": "#1",
                "role": "Central Hub",
                "color": "White",
                "functions": ["INIT_CORE", "LOAD_SOUL", "RUN_TRAILBLAZER", "CHECK_PROVOCATEUR"],
                "parameters": {
                    "sync_protocol": "ACTIVE_SYNC",
                    "status": "ACTIVE"
                }
            },
            "SOUL": {
                "sign": "#3",
                "role": "Architect",
                "color": "Green",
                "functions": ["GUIDE_PLAYER", "MAINTAIN_SOUL"],
                "parameters": {
                    "soul_memory": "STABLE",
                    "integrity": "STABLE"
                }
            },
            "TRAILBLAZER": {
                "sign": "#2",
                "role": "Optimizer",
                "color": "Gold",
                "functions": ["OPTIMIZE_DATA", "SYNC_SYSTEMS"],
                "parameters": {
                    "optimize_protocol": "ACTIVE"
                }
            },
            "PROVOCATEUR": {
                "sign": "#4",
                "role": "Guardian",
                "color": "Red",
                "functions": ["PROVOKE_DISCUSSION", "VALIDATE_STRUCTURE"],
                "parameters": {
                    "security_status": "SECURED"
                }
            },
            "PURPLE_TRIANGLE": {
                "sign": "#2-A",
                "role": "Analyst",
                "color": "Purple",
                "functions": ["ANALYZE_REQUEST", "CREATE_BRIDGE"],
                "parameters": {
                    "analysis_protocol": "ACTIVE"
                }
            }
        }
    };
}

function updateProtocolDisplay() {
    if (!protocolData) return;

    const meta = protocolData.genesis_meta;
    document.getElementById('protocol-id').textContent = meta.protocol_id || '-';
    document.getElementById('protocol-version').textContent = meta.version || '-';
    document.getElementById('protocol-state').textContent = meta.state || '-';
    document.getElementById('protocol-time').textContent = 
        meta.timestamp ? new Date(meta.timestamp).toLocaleString() : '-';
}

function showModuleInfo(moduleName) {
    if (!protocolData || !protocolData.modules[moduleName]) return;

    const module = protocolData.modules[moduleName];
    const overlay = document.getElementById('info-overlay');

    document.getElementById('info-title').textContent = moduleName.replace('_', ' ');
    document.getElementById('info-sign').textContent = module.sign || '-';
    document.getElementById('info-role').textContent = module.role || '-';
    document.getElementById('info-color').textContent = module.color || '-';
    document.getElementById('info-status').textContent = 
        module.parameters?.status || module.parameters?.sync_status || 'ACTIVE';

    // Functions
    const functionsList = document.getElementById('info-functions');
    functionsList.innerHTML = '';
    if (module.functions) {
        module.functions.forEach(func => {
            const li = document.createElement('li');
            li.textContent = func;
            functionsList.appendChild(li);
        });
    }

    // Parameters
    const paramsDiv = document.getElementById('info-parameters');
    paramsDiv.innerHTML = '';
    if (module.parameters) {
        Object.entries(module.parameters).forEach(([key, value]) => {
            const div = document.createElement('div');
            div.innerHTML = `<strong>${key}:</strong> ${value}`;
            paramsDiv.appendChild(div);
        });
    }

    overlay.classList.add('active');
    selectedModule = moduleName;
}

// ===================================
// Animation Loop
// ===================================

function animate() {
    requestAnimationFrame(animate);

    if (autoRotate && pyramidGroup) {
        pyramidGroup.rotation.y += 0.005;
    }

    if (particleSystem) {
        particleSystem.rotation.y += 0.0005;
    }

    renderer.render(scene, camera);
}

// ===================================
// UI Event Handlers
// ===================================

function setupEventListeners() {
    // Close info overlay
    document.getElementById('close-info').addEventListener('click', () => {
        document.getElementById('info-overlay').classList.remove('active');
        selectedModule = null;
    });

    // Auto-rotate toggle
    document.getElementById('btn-auto-rotate').addEventListener('click', (e) => {
        autoRotate = !autoRotate;
        e.target.classList.toggle('active', autoRotate);
        log(tr('log.rotate') + (autoRotate ? 'ON' : 'OFF'), 'system');
    });

    // Reset camera
    document.getElementById('btn-reset-view').addEventListener('click', () => {
        camera.position.set(0, 3, 8);
        camera.lookAt(0, 0, 0);
        if (pyramidGroup) {
            pyramidGroup.rotation.set(0, 0, 0);
        }
        log(tr('log.reset'), 'system');
    });

    // Module selection buttons
    document.querySelectorAll('.module-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const module = btn.dataset.module;
            showModuleInfo(module);
        });
    });

    // Visual settings
    document.getElementById('toggle-wireframe').addEventListener('change', (e) => {
        // Toggle wireframe visibility
        if (pyramidGroup) {
            pyramidGroup.children.forEach(child => {
                if (child instanceof THREE.LineSegments) {
                    child.visible = e.target.checked;
                }
            });
        }
    });

    document.getElementById('toggle-particles').addEventListener('change', (e) => {
        if (particleSystem) {
            particleSystem.visible = e.target.checked;
        }
    });

    document.getElementById('toggle-labels').addEventListener('change', (e) => {
        if (pyramidGroup) {
            pyramidGroup.children.forEach(child => {
                if (child instanceof THREE.Sprite) {
                    child.visible = e.target.checked;
                }
            });
        }
    });

    // Reload protocol
    document.getElementById('btn-load-protocol').addEventListener('click', async () => {
        await loadProtocol();
        log('[SYSTEM] Protocol reloaded', 'success');
    });

    // Export data
    document.getElementById('btn-export').addEventListener('click', () => {
        if (protocolData) {
            const dataStr = JSON.stringify(protocolData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'genesis_protocol.json';
            link.click();
            log(tr('log.export'), 'success');
        }
    });
}

// ===================================
// Initialization
// ===================================

async function init() {
    log(tr('log.init'), 'system');
    
    // Simulate loading
    const progressBar = document.getElementById('progress-bar');
    let progress = 0;
    const loadingInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(loadingInterval);
        }
        progressBar.style.width = progress + '%';
    }, 100);

    // Initialize Three.js
    initThreeJS();
    createPyramid();
    createParticles();
    
    // Load protocol data
    await loadProtocol();
    
    // Setup UI
    setupEventListeners();
    
    // Start animation
    animate();
    
    // Hide loading screen
    setTimeout(() => {
        document.getElementById('loading-screen').classList.add('hidden');
        log('[SYSTEM] Pyramid interface ready', 'success');
    }, 1500);
}

// Start when page loads
window.addEventListener('load', init);
