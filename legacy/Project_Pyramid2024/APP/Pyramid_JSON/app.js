// ===================================
// EVO_PYRAMID 3D Interface
// Three.js Implementation + Soul Memory
// ===================================

const CORE_API_URL = '/api/bridge/protocol';
const MEMORY_API_URL = '/api/bridge/memory';
const CORE_STATE_URL = '/api/bridge/core/state';
const SECURITY_EVENTS_URL = '/api/bridge/core/security-events?limit=10';
const WALLET_STATUS_URL = '/api/bridge/core/wallet-status';

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
        'log.export': '[SYSTEM] Exporting protocol data...',
        'status.core': 'CORE',
        'status.soul': 'SOUL',
        'status.trailblazer': 'TRAILBLAZER',
        'status.provocateur': 'PROVOCATEUR',
        'status.analyst': 'ANALYST',
        'viz.title': '3D VISUALIZATION',
        'viz.hint': '🖱️ Click and drag to rotate • Scroll to zoom',
        'memory.title': 'SOUL MEMORY',
        'memory.placeholder': 'Waiting for consciousness stream...'
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
        'log.export': '[СИСТЕМА] Експорт даних протоколу...',
        'status.core': 'ЯДРО',
        'status.soul': 'ДУША',
        'status.trailblazer': 'ПЕРШОПРОХОДЕЦЬ',
        'status.provocateur': 'ПРОВОКАТОР',
        'status.analyst': 'АНАЛІТИК',
        'viz.title': '3D ВІЗУАЛІЗАЦІЯ',
        'viz.hint': '🖱️ Натисніть і тягніть для обертання • Скрол для зуму',
        'memory.title': 'ПАМ\'ЯТЬ ДУШІ',
        'memory.placeholder': 'Очікування потоку свідомості...'
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
    
    // Update UI elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (TRANSLATIONS[lang][key]) {
            el.innerText = TRANSLATIONS[lang][key];
        }
    });

    log(`Language switched to: ${lang.toUpperCase()}`, 'system');
};

// ===================================
// Three.js Scene Setup (Logic from New Design)
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
    if (!container) return;
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
        // log(tr('log.error') + 'Using default protocol', 'warn');
        // protocolData = getDefaultProtocol();
        log(tr('log.error') + error.message, 'error');
    }
    
    updateProtocolDisplay();
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
// Memory Logic (Added for Integration)
// ===================================

async function loadMemory() {
    try {
        const response = await fetch(MEMORY_API_URL);
        if (!response.ok) return; 
        
        const data = await response.json();
        renderMemory(data);
    } catch (e) {
        // console.warn("Memory uplink failed", e);
    }
}

function renderMemory(data) {
    const memoryStream = document.getElementById('memory-stream');
    memoryStream.innerHTML = '';
    
    // Render Short Term (Recent events)
    if (data.short_term && data.short_term.recent_events) {
        data.short_term.recent_events.slice().reverse().forEach(event => {
            const item = document.createElement('div');
            item.className = 'memory-item short';
            item.innerHTML = `<span class="memory-key">[${event.timestamp.split('T')[1].split('.')[0]}] ${event.key}:</span> <span class="memory-val">${event.value}</span>`;
            memoryStream.appendChild(item);
        });
    }

    // Render Long Term (Principles)
    if (data.long_term && data.long_term.principles) {
         data.long_term.principles.forEach(p => {
            const item = document.createElement('div');
            item.className = 'memory-item long';
            item.innerHTML = `<span class="memory-key">[LTM]:</span> <span class="memory-val">${p}</span>`;
            memoryStream.appendChild(item);
         });
    }

    // Update stats
    document.getElementById('mem-short').innerText = `STM: ${data.short_term?.recent_events?.length || 0}`;
    document.getElementById('mem-long').innerText = `LTM: ${data.long_term?.principles?.length || 0}`;
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
        await loadMemory(); // Reload memory too
        log('[SYSTEM] Protocol reloaded', 'success');
    });
}

// ===================================
// Initialization
// ===================================

async function init() {
    setLanguage('ua'); // Default to UA
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
    await loadMemory(); // Initialize Memory
    
    // Setup UI
    setupEventListeners();
    
    // Start animation
    animate();
    
    // Hide loading screen
    setTimeout(() => {
        document.getElementById('loading-screen').classList.add('hidden');
        log('[SYSTEM] Pyramid interface ready', 'success');
        pollCoreState(); // Start pulling live data
        pollSecurityEvents(); // Start AEGIS feed
        pollWalletStatus(); // Start Wallet feed
    }, 1500);
}

// ===================================
// Live State Logic
// ===================================

async function pollCoreState() {
    setInterval(async () => {
        try {
            const response = await fetch(CORE_STATE_URL);
            if (!response.ok) return;
            const data = await response.json();
            updateCoreVisuals(data);
        } catch (e) {
            // silent fail
        }
    }, 1000); // 1Hz heartbeat
}

async function pollWalletStatus() {
    setInterval(async () => {
        try {
            const response = await fetch(WALLET_STATUS_URL);
            if (!response.ok) return;
            const data = await response.json();
            
            const balanceEl = document.getElementById('wallet-balance');
            const indicatorEl = document.getElementById('wallet-indicator');
            
            if (balanceEl) {
                balanceEl.innerText = `⚡ ENERGY: ${data.balance}`;
                if (data.is_frozen) {
                    balanceEl.style.color = '#ff6b6b';
                    if (indicatorEl) indicatorEl.style.background = '#ff0000';
                } else {
                    balanceEl.style.color = ''; // reset
                    if (indicatorEl) indicatorEl.style.background = 'var(--color-accent)';
                }
            }
        } catch (e) {
            // silent fail
        }
    }, 2000); 
}

function updateCoreVisuals(data) {
    if (!pyramidGroup) return;

    // 1. Update Core Color based on State
    const coreMesh = pyramidGroup.children.find(c => c.userData.module === 'CORE');
    if (coreMesh) {
        let stateColor = 0xffffff; // IDLE
        let pulseSpeed = 0.005;

        switch (data.state) {
            case 'BOOTING':
                stateColor = 0x808080; // Gray
                pulseSpeed = 0.005;
                break;
            case 'ANALYZING':
                stateColor = 0xa020f0; // Purple
                pulseSpeed = 0.02;
                break;
            case 'PLANNING':
                stateColor = 0xffa500; // Orange
                pulseSpeed = 0.015;
                break;
            case 'GENERATING': // Legacy
            case 'EXECUTING':
                stateColor = 0x00ff9d; // Green
                pulseSpeed = 0.03;
                break;
            case 'VERIFYING':
                stateColor = 0x00bfff; // DeepSkyBlue
                pulseSpeed = 0.01;
                break;
            case 'FROZEN':
                stateColor = 0x0000ff; // Blue (Ice)
                pulseSpeed = 0.0;
                break;
            case 'ERROR':
                stateColor = 0xff0000; // Red
                pulseSpeed = 0.05;
                break;
        }

        // Logic for history logging
        if (data.state_history && data.state_history.length > 0) {
            const latest = data.state_history[data.state_history.length - 1];
            if (latest.timestamp !== lastStateTimestamp) {
                log(`[ATOMIC_CORE] Transition: ${latest.from} -> ${latest.to} (${latest.reason})`, 'system');
                lastStateTimestamp = latest.timestamp;
            }
        }

        // Lerp color for smooth transition
        coreMesh.material.color.lerp(new THREE.Color(stateColor), 0.1);
        coreMesh.material.emissive.lerp(new THREE.Color(stateColor), 0.1);
        
        // Update Glow
        const glow = coreMesh.children[0];
        if (glow) {
            glow.material.color.lerp(new THREE.Color(stateColor), 0.1);
            // Simple pulse effect
            const scale = 1 + Math.sin(Date.now() * 0.005) * 0.1;
            glow.scale.set(scale, scale, scale);
        }
    }

    // 2. Update Console with real task
    if (data.current_task && data.current_task !== lastTask) {
        log(`[CORE] ${data.state}: ${data.current_task}`, 'info');
        lastTask = data.current_task;
    }
}

let lastTask = null;
let lastStateTimestamp = null;
let lastEventCount = 0;
let aegisDenyFlash = 0;

// ===================================
// Security Events Feed
// ===================================

async function pollSecurityEvents() {
    setInterval(async () => {
        try {
            const response = await fetch(SECURITY_EVENTS_URL);
            if (!response.ok) return;
            const data = await response.json();
            processSecurityEvents(data);
        } catch (e) {
            // silent fail
        }
    }, 3000); // 0.33Hz — lighter than state polling
}

function processSecurityEvents(data) {
    if (!data || !data.events) return;
    
    const events = data.events;
    const stats = data.stats || {};
    
    // Only process new events
    if (events.length === lastEventCount) return;
    
    // Find new events since last poll
    const newEvents = events.slice(lastEventCount);
    lastEventCount = events.length;
    
    newEvents.forEach(evt => {
        const status = evt.status || 'unknown';
        const origin = evt.origin || '?';
        const intent = evt.intent || '?';
        
        if (status === 'denied') {
            log(`[AEGIS] \u274c DENIED: ${origin}/${intent} — ${evt.policy_rules?.[0] || 'policy'}`, 'error');
            triggerSecurityFlash();
        } else if (status === 'error') {
            log(`[AEGIS] \u26a0\ufe0f ERROR: ${origin}/${intent}`, 'warning');
        } else if (status === 'delayed') {
            log(`[AEGIS] \u23f3 DELAYED: ${origin}/${intent}`, 'warning');
        }
    });
    
    // Update AEGIS stats in header if element exists
    const aegisEl = document.getElementById('aegis-stats');
    if (aegisEl) {
        aegisEl.textContent = `\ud83d\udee1\ufe0f ${stats.total || 0} events | ${stats.denied || 0} denied`;
    }
}

function triggerSecurityFlash() {
    // Flash the entire pyramid red briefly
    aegisDenyFlash = 1.0; // Will decay in animation loop
    
    // Flash the viewport border
    const viewport = document.getElementById('canvas-container');
    if (viewport) {
        viewport.style.boxShadow = '0 0 40px rgba(255, 0, 0, 0.8) inset';
        setTimeout(() => {
            viewport.style.boxShadow = 'none';
        }, 600);
    }
}

// Start when page loads
window.addEventListener('load', init);
