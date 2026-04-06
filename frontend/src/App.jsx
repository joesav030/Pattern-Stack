import { useState, useEffect, useCallback, useRef } from "react";
import STLViewer from "./components/STLViewer.jsx";

const ICONS = {
  cube: "⬜", box: "📦", sphere: "🔵", cylinder: "🥫", cone: "🔺",
  pyramid: "🔺", torus: "🍩", ring: "💍", vase: "🏺", bowl: "🥣",
  cup: "☕", pen_holder: "✏️", phone_stand: "📱", coaster: "⭕",
  gear: "⚙️", hex_nut: "🔩", star: "⭐", heart: "❤️", arrow: "➡️",
  pipe: "🔧", hook: "🪝", keychain: "🗝️", dice: "🎲", planter: "🌱",
};

export default function App() {
  const [query, setQuery] = useState("");
  const [objects, setObjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewingId, setViewingId] = useState(null);
  const [downloading, setDownloading] = useState(null);
  const [toast, setToast] = useState(null);
  const searchRef = useRef(null);

  const fetchObjects = useCallback(async (q) => {
    setLoading(true);
    try {
      const url = q.trim() ? `/api/search?q=${encodeURIComponent(q)}` : "/api/objects";
      const res = await fetch(url);
      const data = await res.json();
      setObjects(data);
    } catch {
      setObjects([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchObjects("");
    searchRef.current?.focus();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => fetchObjects(query), 200);
    return () => clearTimeout(timer);
  }, [query, fetchObjects]);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const handleDownload = async (obj) => {
    setDownloading(obj.id);
    try {
      const res = await fetch(`/api/generate/${obj.id}`);
      if (!res.ok) throw new Error("Generation failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${obj.id}.stl`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast(`Downloaded ${obj.label}.stl`);
    } catch {
      showToast("Download failed — is the backend running?");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0f1117" }}>
      {/* Header */}
      <header style={{
        background: "linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%)",
        borderBottom: "1px solid #1e2536",
        padding: "24px 0 0",
      }}>
        <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
            <span style={{ fontSize: 28 }}>🖨️</span>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: "#e2e8f0" }}>
              STL Generator
            </h1>
          </div>
          <p style={{ margin: "0 0 20px", color: "#64748b", fontSize: 14 }}>
            Search for a 3D object, preview it, and download an STL file ready for your printer.
          </p>

          {/* Search bar */}
          <div style={{ position: "relative", maxWidth: 560 }}>
            <span style={{
              position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)",
              fontSize: 18, color: "#4f6080", pointerEvents: "none",
            }}>🔍</span>
            <input
              ref={searchRef}
              type="text"
              placeholder="Search: cube, vase, phone stand, gear…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                width: "100%", padding: "12px 16px 12px 44px",
                background: "#1a1f2e", border: "2px solid #2d3748",
                borderRadius: 10, color: "#e2e8f0", fontSize: 16,
                outline: "none", transition: "border-color 0.15s",
              }}
              onFocus={(e) => e.target.style.borderColor = "#4f8ef7"}
              onBlur={(e) => e.target.style.borderColor = "#2d3748"}
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                style={{
                  position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                  background: "none", border: "none", color: "#4f6080", cursor: "pointer",
                  fontSize: 18, padding: 2,
                }}
              >
                ×
              </button>
            )}
          </div>

          <div style={{ marginTop: 12, paddingBottom: 16, color: "#4f6080", fontSize: 13 }}>
            {loading ? "Searching…" : `${objects.length} object${objects.length !== 1 ? "s" : ""} found`}
          </div>
        </div>
      </header>

      {/* Object grid */}
      <main style={{ maxWidth: 960, margin: "0 auto", padding: "28px 24px" }}>
        {!loading && objects.length === 0 && (
          <div style={{ textAlign: "center", color: "#4f6080", marginTop: 60 }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🤷</div>
            <div style={{ fontSize: 18 }}>No objects found for "{query}"</div>
            <div style={{ fontSize: 14, marginTop: 6 }}>Try: cube, vase, gear, heart, ring…</div>
          </div>
        )}

        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: 16,
        }}>
          {objects.map((obj) => (
            <ObjectCard
              key={obj.id}
              obj={obj}
              icon={ICONS[obj.id] || "🔷"}
              isDownloading={downloading === obj.id}
              onPreview={() => setViewingId(obj.id)}
              onDownload={() => handleDownload(obj)}
            />
          ))}
        </div>
      </main>

      {/* 3D Viewer modal */}
      {viewingId && (
        <STLViewer objectId={viewingId} onClose={() => setViewingId(null)} />
      )}

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", bottom: 28, left: "50%", transform: "translateX(-50%)",
          background: "#22c55e", color: "#fff", borderRadius: 8,
          padding: "10px 20px", fontSize: 14, fontWeight: 500,
          boxShadow: "0 4px 20px rgba(0,0,0,0.5)", zIndex: 200,
          animation: "fadeIn 0.2s ease",
        }}>
          {toast}
        </div>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateX(-50%) translateY(8px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
      `}</style>
    </div>
  );
}

function ObjectCard({ obj, icon, isDownloading, onPreview, onDownload }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? "#1e2740" : "#151a27",
        border: `1px solid ${hovered ? "#3d5a99" : "#1e2536"}`,
        borderRadius: 12,
        padding: "20px 16px 16px",
        transition: "all 0.18s ease",
        cursor: "default",
        transform: hovered ? "translateY(-2px)" : "none",
        boxShadow: hovered ? "0 8px 24px rgba(0,0,0,0.4)" : "none",
      }}
    >
      <div style={{ fontSize: 36, marginBottom: 10, textAlign: "center" }}>{icon}</div>
      <div style={{ fontWeight: 600, fontSize: 15, color: "#e2e8f0", marginBottom: 4 }}>
        {obj.label}
      </div>
      <div style={{ fontSize: 12, color: "#64748b", marginBottom: 14, lineHeight: 1.4 }}>
        {obj.description}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={onPreview}
          style={{
            flex: 1, padding: "7px 0", background: "#1e3a5f",
            border: "1px solid #2d5a8f", borderRadius: 6,
            color: "#93c5fd", fontSize: 12, fontWeight: 500,
            cursor: "pointer", transition: "background 0.15s",
          }}
          onMouseEnter={(e) => e.target.style.background = "#254875"}
          onMouseLeave={(e) => e.target.style.background = "#1e3a5f"}
        >
          👁 Preview
        </button>
        <button
          onClick={onDownload}
          disabled={isDownloading}
          style={{
            flex: 1, padding: "7px 0",
            background: isDownloading ? "#1a2e4a" : "#1e4a2e",
            border: `1px solid ${isDownloading ? "#2d4a6f" : "#2d7a4f"}`,
            borderRadius: 6,
            color: isDownloading ? "#64748b" : "#86efac",
            fontSize: 12, fontWeight: 500,
            cursor: isDownloading ? "not-allowed" : "pointer",
            transition: "background 0.15s",
          }}
          onMouseEnter={(e) => { if (!isDownloading) e.target.style.background = "#255a38"; }}
          onMouseLeave={(e) => { if (!isDownloading) e.target.style.background = "#1e4a2e"; }}
        >
          {isDownloading ? "⏳ Generating…" : "⬇ Download STL"}
        </button>
      </div>
    </div>
  );
}
