// Global State
let currentAnalysis = null;
let scene, camera, renderer, controls, currentMesh;

document.addEventListener('DOMContentLoaded', () => {
    initThreeJS();
    setupDragAndDrop();
});

// --- Drag & Drop Setup ---
function setupDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('imageInput');
    const fileList = document.getElementById('fileList');
    const analyzeBtn = document.getElementById('analyzeBtn');

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
        dropZone.style.background = 'rgba(44, 130, 167, 0.1)';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        dropZone.style.background = 'transparent';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(45, 40, 155, 0.1)';
        dropZone.style.background = 'transparent';
        
        if (e.dataTransfer.files.length) {
            handleFiles(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFiles(fileInput.files);
        }
    });

    function handleFiles(files) {
        fileList.innerHTML = Array.from(files).map(f => `<div>📄 ${f.name}</div>`).join('');
        analyzeBtn.style.display = 'inline-block';
        
        // Auto upload on analyze click
        analyzeBtn.onclick = () => uploadFiles(files);
    }
}

// --- API Interaction ---
async function uploadFiles(files) {
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.innerText = 'Analyzing...';
    analyzeBtn.disabled = true;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        handleAnalysisResult(data);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during analysis.');
    } finally {
        analyzeBtn.innerText = 'Analyze Images';
        analyzeBtn.disabled = false;
    }
}

function handleAnalysisResult(data) {
    if (!data.results || data.results.length === 0) return;

    // Use the first result for the 3D viewer
    const mainResult = data.results[0];
    currentAnalysis = mainResult;

    // Show Sections
    document.getElementById('explorer').style.display = 'block';
    document.getElementById('report').style.display = 'block';

    // Trigger Resize for Three.js
    resizeViewer();

    // Scroll to Explorer
    document.getElementById('explorer').scrollIntoView({ behavior: 'smooth' });

    // Update 3D Viewer UI
    document.getElementById('modelTitle').innerText = mainResult.organelle.name;
    updateTabContent('overview');

    // Update 3D Model
    update3DModel(mainResult.organelle.name);

    // Generate Reports
    generateReports(data.results);
}

function generateReports(results) {
    const grid = document.getElementById('reportGrid');
    grid.innerHTML = results.map(res => `
        <div class="report-card">
            <h3>${res.filename}</h3>
            <p style="color: var(--primary); margin: 0.5rem 0;">Detected: ${res.organelle.name}</p>
            <div style="font-size: 0.9rem; color: var(--text-muted);">
                <strong>OCR Text:</strong><br>
                ${res.detected_text.join(', ')}
            </div>
            <div class="confidence-meter">
                <div class="confidence-fill" style="width: ${res.confidence * 100}%"></div>
            </div>
            <div style="text-align: right; margin-top: 0.5rem; font-size: 0.8rem; color: var(--success);">
                ${Math.round(res.confidence * 100)}% Confidence
            </div>
        </div>
    `).join('');
}

// --- Tabs ---
function switchTab(tabName) {
    // Update active tab UI
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    updateTabContent(tabName);
}

function updateTabContent(tabName) {
    if (!currentAnalysis) return;
    const content = document.getElementById('tabContent');
    const data = currentAnalysis.organelle;

    switch(tabName) {
        case 'overview':
            content.innerText = data.function;
            break;
        case 'structure':
            content.innerText = data.structure;
            break;
        case 'function':
            content.innerText = `Fun Fact: ${data.fun_fact}\n\nDiseases: ${data.diseases}`;
            break;
    }
}

// --- Three.js Viewer ---
function initThreeJS() {
    const container = document.getElementById('viewer');
    
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    // Add some fog for depth
    scene.fog = new THREE.FogExp2(0x000000, 0.035);

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0, 8);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x38bdf8, 2, 50);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xc084fc, 2, 50);
    pointLight2.position.set(-5, -5, 5);
    scene.add(pointLight2);

    // Initial Animation Loop
    animate();

    // Resize handler
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
}

function update3DModel(organelleName) {
    if (currentMesh) {
        scene.remove(currentMesh);
    }

    let geometry, material;
    let group = new THREE.Group(); // Use a group to combine complex shapes

    // Normalize name for matching
    const name = organelleName.toLowerCase();

    if (name.includes('mitochondria')) {
        // Mitochondria: Capsule with internal folds (implied by texture/color)
        geometry = new THREE.CapsuleGeometry(1, 3, 4, 8);
        material = new THREE.MeshStandardMaterial({ 
            color: 0xff7eb3, roughness: 0.3, metalness: 0.2, emissive: 0x550022, emissiveIntensity: 0.2
        });
        currentMesh = new THREE.Mesh(geometry, material);

    } else if (name.includes('chloroplast')) {
        // Chloroplast: Green Disc/Cylinder
        geometry = new THREE.CylinderGeometry(2, 2, 0.5, 32);
        material = new THREE.MeshStandardMaterial({ 
            color: 0x4ade80, roughness: 0.4, metalness: 0.1 
        });
        currentMesh = new THREE.Mesh(geometry, material);
        // Add "stacks" inside
        const stackGeo = new THREE.CylinderGeometry(0.3, 0.3, 0.6, 8);
        const stackMat = new THREE.MeshStandardMaterial({ color: 0x228b22 });
        for(let i=0; i<5; i++) {
            const stack = new THREE.Mesh(stackGeo, stackMat);
            stack.position.set(Math.sin(i)*1, 0.3, Math.cos(i)*1);
            currentMesh.add(stack);
        }

    } else if (name.includes('ribosome')) {
        // Ribosomes: Two subunits (Cluster of spheres)
        const largeSubunitGeo = new THREE.SphereGeometry(1.2, 32, 32);
        const smallSubunitGeo = new THREE.SphereGeometry(0.8, 32, 32);
        
        material = new THREE.MeshStandardMaterial({ color: 0xffa500, roughness: 0.5 }); // Orange
        
        const large = new THREE.Mesh(largeSubunitGeo, material);
        const small = new THREE.Mesh(smallSubunitGeo, material);
        small.position.y = 1.2;
        
        group.add(large);
        group.add(small);
        currentMesh = group;

    } else if (name.includes('endoplasmic') || name.includes('er')) {
        // ER: Folded sheets (Torus Knot as approximation)
        geometry = new THREE.TorusKnotGeometry(1.5, 0.4, 100, 16);
        material = new THREE.MeshStandardMaterial({ 
            color: 0xff69b4, roughness: 0.3, metalness: 0.1 
        }); // Pinkish
        currentMesh = new THREE.Mesh(geometry, material);

    } else if (name.includes('golgi')) {
        // Golgi: Stack of flattened sacs (scaled toruses or cylinders)
        material = new THREE.MeshStandardMaterial({ color: 0xdda0dd, roughness: 0.2 }); // Plum
        currentMesh = new THREE.Group();
        
        for (let i = 0; i < 5; i++) {
            const sacGeo = new THREE.CylinderGeometry(2 - (i*0.2), 2 - (i*0.2), 0.2, 32);
            const sac = new THREE.Mesh(sacGeo, material);
            sac.position.y = (i - 2) * 0.4;
            sac.scale.z = 0.5; // Flatten
            currentMesh.add(sac);
        }

    } else if (name.includes('lysosome')) {
        // Lysosome: Simple sphere with "enzymes" inside (glowing core)
        geometry = new THREE.SphereGeometry(1.5, 32, 32);
        material = new THREE.MeshPhysicalMaterial({ 
            color: 0xffff00, transmission: 0.5, opacity: 0.8, transparent: true, roughness: 0 
        }); // Yellow Glassy
        currentMesh = new THREE.Mesh(geometry, material);
        
        // Inner core
        const core = new THREE.Mesh(new THREE.SphereGeometry(0.8), new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 0.5 }));
        currentMesh.add(core);

    } else if (name.includes('membrane')) {
        // Cell Membrane: Wavy surface
        geometry = new THREE.PlaneGeometry(5, 5, 10, 10);
        // Deform vertices to make it wavy
        const posAttribute = geometry.attributes.position;
        for (let i = 0; i < posAttribute.count; i++) {
            const z = 0.5 * Math.sin(posAttribute.getX(i) * 2) * Math.sin(posAttribute.getY(i) * 2);
            posAttribute.setZ(i, z);
        }
        geometry.computeVertexNormals();
        
        material = new THREE.MeshStandardMaterial({ 
            color: 0x87ceeb, side: THREE.DoubleSide, transparent: true, opacity: 0.6 
        });
        currentMesh = new THREE.Mesh(geometry, material);

    } else if (name.includes('wall')) {
        // Cell Wall: Rigid box/structure
        geometry = new THREE.BoxGeometry(3, 3, 3);
        // Wireframe heavy look
        material = new THREE.MeshStandardMaterial({ 
            color: 0x2e8b57, wireframe: true 
        });
        const innerMat = new THREE.MeshStandardMaterial({ 
            color: 0x2e8b57, transparent: true, opacity: 0.1 
        });
        currentMesh = new THREE.Mesh(geometry, innerMat);
        currentMesh.add(new THREE.LineSegments(new THREE.WireframeGeometry(geometry), new THREE.LineBasicMaterial({ color: 0x00ff00 })));

    } else {
        // Nucleus (Default): Sphere with pores
        geometry = new THREE.SphereGeometry(2, 32, 32);
        material = new THREE.MeshStandardMaterial({ 
            color: 0x818cf8, roughness: 0.2, metalness: 0.5 
        });
        currentMesh = new THREE.Mesh(geometry, material);
        
        // Nucleolus
        const nucGeo = new THREE.SphereGeometry(0.8, 16, 16);
        const nucMat = new THREE.MeshStandardMaterial({ color: 0x4b0082 });
        const nucleolus = new THREE.Mesh(nucGeo, nucMat);
        currentMesh.add(nucleolus); // Won't be visible unless outer is transparent, but conceptually there
    }

    // Add common glow/wireframe to all meshes for consistency
    if (!name.includes('wall')) { // Wall already has wireframe
        // Bounding box wrapper for consistent effect
        const box = new THREE.Box3().setFromObject(currentMesh);
        const size = new THREE.Vector3();
        box.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);
        
        // Add subtle outer glow
        const glowGeo = new THREE.SphereGeometry(maxDim * 0.7, 32, 32);
        const glowMat = new THREE.MeshBasicMaterial({ 
            color: 0xffffff, transparent: true, opacity: 0.05, side: THREE.BackSide 
        });
        currentMesh.add(new THREE.Mesh(glowGeo, glowMat));
    }

    scene.add(currentMesh);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    
    if (currentMesh) {
        currentMesh.rotation.y += 0.005;
        currentMesh.rotation.x += 0.002;
    }
    
    renderer.render(scene, camera);
}

function resizeViewer() {
    const container = document.getElementById('viewer');
    if (!container || !camera || !renderer) return;

    // Small delay to ensure display:block has taken effect
    setTimeout(() => {
        const width = container.clientWidth;
        const height = container.clientHeight;

        if (width === 0 || height === 0) return;

        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    }, 50);
}
