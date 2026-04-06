import { useEffect, useRef } from "react";
import * as THREE from "three";

function parseSTL(buffer) {
  // Binary STL: starts with 80-byte header, then uint32 triangle count
  const view = new DataView(buffer);
  const numTriangles = view.getUint32(80, true);
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(numTriangles * 9);
  const normals = new Float32Array(numTriangles * 9);

  let offset = 84;
  for (let i = 0; i < numTriangles; i++) {
    const nx = view.getFloat32(offset, true);
    const ny = view.getFloat32(offset + 4, true);
    const nz = view.getFloat32(offset + 8, true);
    offset += 12;

    for (let v = 0; v < 3; v++) {
      const vi = i * 9 + v * 3;
      positions[vi]     = view.getFloat32(offset, true);
      positions[vi + 1] = view.getFloat32(offset + 4, true);
      positions[vi + 2] = view.getFloat32(offset + 8, true);
      normals[vi]     = nx;
      normals[vi + 1] = ny;
      normals[vi + 2] = nz;
      offset += 12;
    }
    offset += 2; // attribute byte count
  }

  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
  geometry.computeBoundingBox();
  return geometry;
}

export default function STLViewer({ objectId, onClose }) {
  const canvasRef = useRef(null);
  const stateRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    // Scene setup
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1f2e);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    camera.position.set(0, 60, 160);

    // Lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambient);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(80, 120, 80);
    dirLight.castShadow = true;
    scene.add(dirLight);
    const fillLight = new THREE.DirectionalLight(0x6699ff, 0.3);
    fillLight.position.set(-80, -40, -80);
    scene.add(fillLight);

    // Grid
    const grid = new THREE.GridHelper(200, 20, 0x333344, 0x222233);
    grid.position.y = -40;
    scene.add(grid);

    let meshObj = null;
    let animId = null;
    let autoRotate = true;
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };
    let spherical = { theta: 0.3, phi: Math.PI / 3, radius: 160 };

    function updateCamera() {
      camera.position.set(
        spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta),
        spherical.radius * Math.cos(spherical.phi),
        spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta)
      );
      camera.lookAt(0, 0, 0);
    }
    updateCamera();

    function animate() {
      animId = requestAnimationFrame(animate);
      if (autoRotate && !isDragging) {
        spherical.theta += 0.006;
        updateCamera();
      }
      renderer.render(scene, camera);
    }
    animate();

    // Mouse orbit controls
    canvas.addEventListener("mousedown", (e) => {
      isDragging = true;
      autoRotate = false;
      prevMouse = { x: e.clientX, y: e.clientY };
    });
    canvas.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;
      spherical.theta -= dx * 0.008;
      spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi + dy * 0.008));
      updateCamera();
      prevMouse = { x: e.clientX, y: e.clientY };
    });
    canvas.addEventListener("mouseup", () => { isDragging = false; });
    canvas.addEventListener("mouseleave", () => { isDragging = false; });
    canvas.addEventListener("wheel", (e) => {
      spherical.radius = Math.max(40, Math.min(500, spherical.radius + e.deltaY * 0.3));
      updateCamera();
    });

    // Touch support
    let lastTouch = null;
    canvas.addEventListener("touchstart", (e) => {
      isDragging = true;
      autoRotate = false;
      lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    });
    canvas.addEventListener("touchmove", (e) => {
      if (!isDragging || !lastTouch) return;
      e.preventDefault();
      const dx = e.touches[0].clientX - lastTouch.x;
      const dy = e.touches[0].clientY - lastTouch.y;
      spherical.theta -= dx * 0.008;
      spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi + dy * 0.008));
      updateCamera();
      lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }, { passive: false });
    canvas.addEventListener("touchend", () => { isDragging = false; });

    // Load STL
    fetch(`/api/generate/${objectId}`)
      .then((r) => r.arrayBuffer())
      .then((buffer) => {
        const geometry = parseSTL(buffer);
        geometry.center();

        const material = new THREE.MeshPhongMaterial({
          color: 0x4f8ef7,
          specular: 0x334466,
          shininess: 60,
          flatShading: false,
        });
        meshObj = new THREE.Mesh(geometry, material);
        meshObj.castShadow = true;
        meshObj.receiveShadow = true;

        // Scale to fit view
        geometry.computeBoundingBox();
        const box = geometry.boundingBox;
        const size = new THREE.Vector3();
        box.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 80 / maxDim;
        meshObj.scale.setScalar(scale);

        scene.add(meshObj);
      })
      .catch(console.error);

    stateRef.current = { renderer, animId };

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, [objectId]);

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 100,
    }}>
      <div style={{
        width: "min(90vw, 800px)", background: "#1a1f2e",
        borderRadius: 16, overflow: "hidden", boxShadow: "0 25px 80px rgba(0,0,0,0.7)",
        border: "1px solid #2d3748",
      }}>
        <div style={{
          padding: "14px 20px", display: "flex", justifyContent: "space-between",
          alignItems: "center", borderBottom: "1px solid #2d3748",
        }}>
          <span style={{ fontWeight: 600, color: "#a0aec0", fontSize: 14 }}>
            3D Preview — drag to rotate · scroll to zoom
          </span>
          <button
            onClick={onClose}
            style={{
              background: "none", border: "none", color: "#a0aec0",
              fontSize: 22, cursor: "pointer", lineHeight: 1, padding: "0 4px",
            }}
          >
            ×
          </button>
        </div>
        <canvas
          ref={canvasRef}
          style={{ display: "block", width: "100%", height: "min(60vw, 480px)", cursor: "grab" }}
          width={800}
          height={480}
        />
      </div>
    </div>
  );
}
