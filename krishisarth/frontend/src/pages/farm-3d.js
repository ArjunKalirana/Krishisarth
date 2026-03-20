import { t } from '../utils/i18n.js';
import { store } from '../state/store.js';
import { api } from '../api/client.js';

/**
 * 3D Farm View — Interactive Three.js visualization of farm zones.
 * Shows each zone as a 3D plot with color indicating moisture status.
 * Moisture: red=dry, green=optimal, blue=wet
 */
export function renderFarm3D() {
    const container = document.createElement('div');
    container.className = 'space-y-6 animate-in fade-in duration-500';

    container.innerHTML = `
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
                <h1 class="text-3xl font-extrabold text-gray-900">
                    ${t('farm3d_title')} <span class="brand-text">🌾</span>
                </h1>
                <p class="text-gray-500 font-medium mt-1">${t('farm3d_subtitle')}</p>
            </div>
            <div class="flex gap-4 items-center flex-wrap">
                <div class="flex gap-3 text-xs font-bold">
                    <span class="flex items-center gap-1">
                        <div class="w-3 h-3 rounded-sm" style="background:#ef4444"></div> ${t('dash_dry')}
                    </span>
                    <span class="flex items-center gap-1">
                        <div class="w-3 h-3 rounded-sm" style="background:#22c55e"></div> ${t('dash_optimal')}
                    </span>
                    <span class="flex items-center gap-1">
                        <div class="w-3 h-3 rounded-sm" style="background:#3b82f6"></div> ${t('dash_wet')}
                    </span>
                    <span class="flex items-center gap-1">
                        <div class="w-3 h-3 rounded-sm animate-pulse" style="background:#1a7a4a"></div>
                        ${t('dash_irrigating')}
                    </span>
                </div>
            </div>
        </div>

        <!-- 3D Canvas -->
        <div class="ks-card overflow-hidden" style="height: 520px; position: relative;">
            <canvas id="farm3d-canvas" style="width:100%; height:100%; display:block;"></canvas>
            <div id="farm3d-overlay" style="
                position:absolute; top:12px; left:50%; transform:translateX(-50%);
                background:rgba(0,0,0,0.5); color:white; padding:6px 16px;
                border-radius:99px; font-size:11px; font-weight:700; pointer-events:none;
                white-space:nowrap;
            ">${t('farm3d_rotate')}</div>
            <div id="farm3d-tooltip" style="
                position:absolute; display:none;
                background:rgba(0,0,0,0.85); color:white;
                padding:10px 14px; border-radius:10px;
                font-size:12px; font-weight:600; pointer-events:none;
                min-width:160px; line-height:1.8;
            "></div>
            <div id="farm3d-loading" style="
                position:absolute; inset:0; display:flex; align-items:center;
                justify-content:center; background:#f0f7f3;
                flex-direction:column; gap:12px;
            ">
                <div style="width:40px;height:40px;border:4px solid #dcfce7;border-top-color:#1a7a4a;border-radius:50%;animation:spin 0.8s linear infinite;"></div>
                <p style="font-size:12px;color:#6b7280;font-weight:700;">${t('farm3d_loading')}</p>
            </div>
        </div>

        <!-- Zone info cards below 3D view -->
        <div id="zone-info-grid" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3"></div>

        <style>
            @keyframes spin { to { transform: rotate(360deg); } }
        </style>
    `;

    // Load Three.js and render after DOM is ready
    setTimeout(() => _init3D(container), 100);

    return container;
}

async function _init3D(container) {
    const farm = store.getState('currentFarm');
    const loadingEl = container.querySelector('#farm3d-loading');
    const infoGrid  = container.querySelector('#zone-info-grid');

    if (!farm?.id) {
        if (loadingEl) loadingEl.innerHTML = `<p style="color:#6b7280;font-weight:700;">${t('farm3d_no_farm')}</p>`;
        return;
    }

    // Fetch real zone data
    let zones = [];
    try {
        const res = await api(`/farms/${farm.id}/dashboard`);
        zones = res?.data?.zones || [];
    } catch {
        try {
            const res = await api(`/farms/${farm.id}/`);
            zones = (res?.data?.zones || []).map(z => ({
                ...z, moisture_pct: 0, moisture_status: 'ok', pump_running: false
            }));
        } catch { /* no data */ }
    }

    if (zones.length === 0) {
        if (loadingEl) loadingEl.innerHTML = `<p style="color:#6b7280;font-weight:700;">${t('dash_no_zones')}</p>`;
        return;
    }

    // Load Three.js from CDN
    await _loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js');

    const canvas = container.querySelector('#farm3d-canvas');
    if (!canvas || !window.THREE) return;
    if (loadingEl) loadingEl.style.display = 'none';

    const THREE = window.THREE;

    // ── Scene setup ──────────────────────────────────────────────────────────
    const scene    = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f7f3);

    const w = canvas.clientWidth  || 800;
    const h = canvas.clientHeight || 520;

    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
    camera.position.set(0, 18, 22);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(w, h);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // ── Lighting ─────────────────────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));

    const sun = new THREE.DirectionalLight(0xfff5e0, 1.2);
    sun.position.set(10, 20, 10);
    sun.castShadow = true;
    sun.shadow.mapSize.width  = 2048;
    sun.shadow.mapSize.height = 2048;
    scene.add(sun);

    scene.add(new THREE.HemisphereLight(0x87ceeb, 0x228b22, 0.3));

    // ── Ground plane ─────────────────────────────────────────────────────────
    const groundGeo = new THREE.PlaneGeometry(40, 40);
    const groundMat = new THREE.MeshLambertMaterial({ color: 0xc8e6c9 });
    const ground    = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.05;
    ground.receiveShadow = true;
    scene.add(ground);

    // Grid lines on ground
    const grid = new THREE.GridHelper(40, 20, 0x9e9e9e, 0xd0d0d0);
    grid.position.y = 0;
    scene.add(grid);

    // ── Farm boundary fence ───────────────────────────────────────────────────
    const fenceMat = new THREE.MeshLambertMaterial({ color: 0x8d6e63 });
    [[0, 20, 20, 0.3, 0.4], [0, -20, 20, 0.3, 0.4],
     [20, 0, 0.3, 20, 0.4], [-20, 0, 0.3, 20, 0.4]].forEach(([x, z, w, d, h]) => {
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), fenceMat);
        mesh.position.set(x, 0.2, z);
        scene.add(mesh);
    });

    // ── Zone blocks ───────────────────────────────────────────────────────────
    const meshes = [];
    const cols   = Math.ceil(Math.sqrt(zones.length));
    const spacing = 7;
    const offset  = (cols - 1) * spacing / 2;

    const _zoneColor = (z) => {
        if (z.pump_running)           return 0x1a7a4a; // pulsing green
        if (z.moisture_status === 'dry')  return 0xef4444;
        if (z.moisture_status === 'wet')  return 0x3b82f6;
        return 0x22c55e; // optimal
    };

    zones.forEach((zone, i) => {
        const row = Math.floor(i / cols);
        const col = i % cols;
        const x   = col * spacing - offset;
        const z   = row * spacing - offset;

        const moisture = zone.moisture_pct || 0;
        const height   = Math.max(0.4, (moisture / 100) * 3.5 + 0.3);

        // Soil base
        const baseMesh = new THREE.Mesh(
            new THREE.BoxGeometry(5.5, 0.3, 5.5),
            new THREE.MeshLambertMaterial({ color: 0x795548 })
        );
        baseMesh.position.set(x, 0.15, z);
        baseMesh.castShadow = true;
        baseMesh.receiveShadow = true;
        scene.add(baseMesh);

        // Crop block — height represents moisture level
        const color   = _zoneColor(zone);
        const cropMat = new THREE.MeshLambertMaterial({ color, transparent: true, opacity: 0.88 });
        const cropMesh = new THREE.Mesh(new THREE.BoxGeometry(5, height, 5), cropMat);
        cropMesh.position.set(x, 0.3 + height / 2, z);
        cropMesh.castShadow = true;
        cropMesh.userData = { zone, originalColor: color, originalY: 0.3 + height / 2 };
        scene.add(cropMesh);
        meshes.push(cropMesh);

        // Moisture indicator particles (small spheres on top)
        if (moisture > 5) {
            const dotCount = Math.floor(moisture / 20) + 1;
            for (let d = 0; d < dotCount; d++) {
                const dot = new THREE.Mesh(
                    new THREE.SphereGeometry(0.12, 6, 6),
                    new THREE.MeshLambertMaterial({ color: 0x60a5fa })
                );
                dot.position.set(
                    x + (Math.random() - 0.5) * 4,
                    0.3 + height + 0.2,
                    z + (Math.random() - 0.5) * 4
                );
                scene.add(dot);
            }
        }

        // Zone label (canvas texture)
        const labelSprite = _makeLabel(zone.name, color);
        labelSprite.position.set(x, 0.3 + height + 1.2, z);
        labelSprite.scale.set(4, 1.2, 1);
        scene.add(labelSprite);

        // Pump indicator
        if (zone.pump_running) {
            const pump = new THREE.Mesh(
                new THREE.CylinderGeometry(0.2, 0.2, 1.5, 8),
                new THREE.MeshLambertMaterial({ color: 0x06b6d4 })
            );
            pump.position.set(x + 2.5, 0.3 + height + 0.75, z + 2.5);
            scene.add(pump);
        }
    });

    // ── Zone info cards ───────────────────────────────────────────────────────
    infoGrid.innerHTML = zones.map(z => {
        const color = z.moisture_status === 'dry' ? '#ef4444' :
                      z.moisture_status === 'wet' ? '#3b82f6' : '#22c55e';
        const label = z.moisture_status === 'dry' ? t('dash_dry') :
                      z.moisture_status === 'wet' ? t('dash_wet') : t('dash_optimal');
        return `
            <div class="ks-card p-4 text-center border-t-4" style="border-top-color:${color}">
                <p class="text-[9px] font-black text-gray-400 uppercase tracking-widest truncate">${z.name}</p>
                <p class="text-2xl font-black mt-1" style="color:${color}">${(z.moisture_pct || 0).toFixed(0)}%</p>
                <p class="text-[9px] font-bold mt-1" style="color:${color}">${label}</p>
                ${z.pump_running ? `<p class="text-[9px] font-black text-green-600 mt-1 animate-pulse">💧 ${t('farm3d_running')}</p>` : ''}
            </div>
        `;
    }).join('');

    // ── Mouse interaction ──────────────────────────────────────────────────────
    const raycaster = new THREE.Raycaster();
    const mouse     = new THREE.Vector2();
    const tooltip   = container.querySelector('#farm3d-tooltip');
    let   hovered   = null;

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouse.x =  ((e.clientX - rect.left) / rect.width)  * 2 - 1;
        mouse.y = -((e.clientY - rect.top)  / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const hits = raycaster.intersectObjects(meshes);

        // Reset previous hover
        if (hovered && hits[0]?.object !== hovered) {
            hovered.material.emissive?.setHex(0x000000);
            hovered = null;
            tooltip.style.display = 'none';
        }

        if (hits.length > 0) {
            const mesh = hits[0].object;
            if (mesh !== hovered) {
                hovered = mesh;
                mesh.material.emissive?.setHex(0x444444);
                const z = mesh.userData.zone;
                tooltip.style.display = 'block';
                tooltip.innerHTML = `
                    <div style="font-size:13px;font-weight:800;margin-bottom:4px;">${z.name}</div>
                    <div>${t('farm3d_moisture')}: <b>${(z.moisture_pct || 0).toFixed(1)}%</b></div>
                    <div>${t('farm3d_status')}: <b>${z.moisture_status?.toUpperCase() || 'N/A'}</b></div>
                    <div>${t('farm3d_pump')}: <b>${z.pump_running ? t('farm3d_running') : t('farm3d_stopped')}</b></div>
                    ${z.temp_c   ? `<div>${t('farm3d_temp')}: <b>${z.temp_c.toFixed(1)}°C</b></div>` : ''}
                    ${z.ec_ds_m  ? `<div>${t('farm3d_ec')}: <b>${z.ec_ds_m.toFixed(2)} dS/m</b></div>` : ''}
                `;
            }
            tooltip.style.left = (e.clientX - canvas.getBoundingClientRect().left + 16) + 'px';
            tooltip.style.top  = (e.clientY - canvas.getBoundingClientRect().top  - 10) + 'px';
        }
    });

    canvas.addEventListener('mouseleave', () => {
        if (hovered) {
            hovered.material.emissive?.setHex(0x000000);
            hovered = null;
        }
        tooltip.style.display = 'none';
    });

    // ── Orbit controls (manual implementation — no OrbitControls available) ──
    let isDragging = false, prevX = 0, prevY = 0;
    let rotY = 0, rotX = 0.4, radius = 28;

    const updateCamera = () => {
        camera.position.x = radius * Math.sin(rotY) * Math.cos(rotX);
        camera.position.y = radius * Math.sin(rotX) + 5;
        camera.position.z = radius * Math.cos(rotY) * Math.cos(rotX);
        camera.lookAt(0, 2, 0);
    };
    updateCamera();

    canvas.addEventListener('mousedown', (e) => { isDragging = true; prevX = e.clientX; prevY = e.clientY; });
    window.addEventListener('mouseup',   () => { isDragging = false; });
    canvas.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        rotY += (e.clientX - prevX) * 0.008;
        rotX  = Math.max(0.1, Math.min(1.2, rotX - (e.clientY - prevY) * 0.005));
        prevX = e.clientX;
        prevY = e.clientY;
        updateCamera();
    });

    canvas.addEventListener('wheel', (e) => {
        radius = Math.max(10, Math.min(50, radius + e.deltaY * 0.05));
        updateCamera();
        e.preventDefault();
    }, { passive: false });

    // Touch support for mobile
    let lastTouchX = 0, lastTouchY = 0;
    canvas.addEventListener('touchstart', (e) => {
        lastTouchX = e.touches[0].clientX;
        lastTouchY = e.touches[0].clientY;
    });
    canvas.addEventListener('touchmove', (e) => {
        rotY += (e.touches[0].clientX - lastTouchX) * 0.008;
        rotX  = Math.max(0.1, Math.min(1.2, rotX - (e.touches[0].clientY - lastTouchY) * 0.005));
        lastTouchX = e.touches[0].clientX;
        lastTouchY = e.touches[0].clientY;
        updateCamera();
        e.preventDefault();
    }, { passive: false });

    // ── Animation loop ────────────────────────────────────────────────────────
    let frame = 0;
    let animId;

    const animate = () => {
        animId = requestAnimationFrame(animate);
        frame++;

        // Pulse pumping zones
        meshes.forEach(m => {
            if (m.userData.zone?.pump_running) {
                const pulse = Math.sin(frame * 0.08) * 0.15 + 1;
                m.scale.set(pulse, 1, pulse);
            }
        });

        renderer.render(scene, camera);
    };
    animate();

    // Cleanup when page navigates away
    window.addEventListener('hashchange', () => {
        cancelAnimationFrame(animId);
        renderer.dispose();
    }, { once: true });

    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });
    resizeObserver.observe(canvas);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function _makeLabel(text, color) {
    const canvas = document.createElement('canvas');
    canvas.width  = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(0,0,0,0)';
    ctx.fillRect(0, 0, 256, 64);
    ctx.fillStyle = '#' + color.toString(16).padStart(6, '0');
    ctx.font = 'bold 22px DM Sans, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    // Background pill
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.roundRect(8, 12, 240, 40, 8);
    ctx.fill();
    ctx.fillStyle = '#1a1a1a';
    ctx.fillText(text.length > 14 ? text.slice(0, 14) + '…' : text, 128, 32);
    const texture = new window.THREE.CanvasTexture(canvas);
    const mat     = new window.THREE.SpriteMaterial({ map: texture, transparent: true });
    return new window.THREE.Sprite(mat);
}

function _loadScript(src) {
    return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${src}"]`)) {
            resolve();
            return;
        }
        const s = document.createElement('script');
        s.src = src;
        s.onload  = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
    });
}
