import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Network, Search, Loader2, Play, X, GitBranch, Boxes, Share2, Filter, ZoomIn, ZoomOut, Maximize2, ArrowRight } from "lucide-react";
import api from "../services/api";

// ── Types ────────────────────────────────────────────────────────────────────

type GraphNode = {
  id: string;
  name: string;
  type: string;
  description: string;
  doc_source?: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
};

type GraphEdge = {
  source: string;
  target: string;
  relation: string;
};

type GraphStats = {
  nodes: number;
  edges: number;
  loaded: boolean;
};

// ── Color palette for entity types ───────────────────────────────────────────

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  PERSON:       { bg: "#3b82f6", border: "#60a5fa", text: "#dbeafe", glow: "rgba(59,130,246,0.4)" },
  ORGANIZATION: { bg: "#8b5cf6", border: "#a78bfa", text: "#ede9fe", glow: "rgba(139,92,246,0.4)" },
  TECHNOLOGY:   { bg: "#10b981", border: "#34d399", text: "#d1fae5", glow: "rgba(16,185,129,0.4)" },
  CONCEPT:      { bg: "#f59e0b", border: "#fbbf24", text: "#fef3c7", glow: "rgba(245,158,11,0.4)" },
  LOCATION:     { bg: "#ef4444", border: "#f87171", text: "#fee2e2", glow: "rgba(239,68,68,0.4)" },
  EVENT:        { bg: "#ec4899", border: "#f472b6", text: "#fce7f3", glow: "rgba(236,72,153,0.4)" },
  unknown:      { bg: "#64748b", border: "#94a3b8", text: "#e2e8f0", glow: "rgba(100,116,139,0.3)" },
};

function getTypeColor(type: string) {
  return TYPE_COLORS[type] || TYPE_COLORS.unknown;
}

// ── Component ────────────────────────────────────────────────────────────────

export default function KnowledgeGraphPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animFrameRef = useRef<number | undefined>(undefined);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [search, setSearch] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [building, setBuilding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 });
  const [buildResult, setBuildResult] = useState<any>(null);

  // Zoom & Pan state
  const [zoom, setZoom] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const isPanningRef = useRef(false);
  const panStartRef = useRef({ x: 0, y: 0 });

  const dragRef = useRef<{ node: GraphNode | null; offsetX: number; offsetY: number }>({
    node: null, offsetX: 0, offsetY: 0,
  });

  // ── Responsive canvas sizing ─────────────────────────────────────────────

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setCanvasSize({
          width: Math.floor(width * window.devicePixelRatio),
          height: Math.floor(height * window.devicePixelRatio),
        });
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // ── Derived data ─────────────────────────────────────────────────────────

  const entityTypes = useMemo(() => {
    const types = new Map<string, number>();
    nodes.forEach((n) => {
      types.set(n.type, (types.get(n.type) || 0) + 1);
    });
    return types;
  }, [nodes]);

  const connectionCounts = useMemo(() => {
    const counts = new Map<string, number>();
    edges.forEach((e) => {
      counts.set(e.source, (counts.get(e.source) || 0) + 1);
      counts.set(e.target, (counts.get(e.target) || 0) + 1);
    });
    return counts;
  }, [edges]);

  const selectedNeighbors = useMemo(() => {
    if (!selectedNode) return { incoming: [] as GraphEdge[], outgoing: [] as GraphEdge[] };
    return {
      incoming: edges.filter((e) => e.target === selectedNode.id),
      outgoing: edges.filter((e) => e.source === selectedNode.id),
    };
  }, [selectedNode, edges]);

  // ── Data fetching ────────────────────────────────────────────────────────

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const [graphRes, statsRes] = await Promise.all([
        api.get("/kg/graph"),
        api.get("/kg/stats"),
      ]);

      const rawNodes = graphRes.data.nodes || [];
      const rawEdges = graphRes.data.edges || [];

      const cx = canvasSize.width / (2 * window.devicePixelRatio);
      const cy = canvasSize.height / (2 * window.devicePixelRatio);

      const initialized: GraphNode[] = rawNodes.map((n: any, i: number) => ({
        ...n,
        x: cx + Math.cos(i * 2.4 + Math.random() * 0.5) * (120 + Math.random() * 200),
        y: cy + Math.sin(i * 2.4 + Math.random() * 0.5) * (120 + Math.random() * 200),
        vx: 0,
        vy: 0,
      }));

      setNodes(initialized);
      setEdges(rawEdges);
      setStats(statsRes.data);
    } catch (err) {
      console.error("Failed to fetch graph:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBuild = async () => {
    setBuilding(true);
    setBuildResult(null);
    try {
      const res = await api.post("/kg/build");
      setBuildResult(res.data);
      await fetchGraph();
    } catch (err) {
      console.error("Build failed:", err);
    } finally {
      setBuilding(false);
    }
  };

  useEffect(() => { fetchGraph(); }, []);

  // ── Filter logic ─────────────────────────────────────────────────────────

  const toggleFilter = (type: string) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const isNodeVisible = (node: GraphNode): boolean => {
    if (activeFilters.size > 0 && !activeFilters.has(node.type)) return false;
    return true;
  };

  // ── Zoom helpers ─────────────────────────────────────────────────────────

  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.25, 4));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.25, 0.25));
  const handleFitView = () => {
    setZoom(1);
    setPanOffset({ x: 0, y: 0 });
  };

  // ── Screen ↔ world coordinate conversion ─────────────────────────────────

  const screenToWorld = (sx: number, sy: number) => ({
    x: (sx - panOffset.x) / zoom,
    y: (sy - panOffset.y) / zoom,
  });

  // ── Force simulation ──────────────────────────────────────────────────────

  const simulate = useCallback(() => {
    if (nodes.length === 0) return;

    const w = canvasSize.width / window.devicePixelRatio;
    const h = canvasSize.height / window.devicePixelRatio;
    const centerX = w / 2;
    const centerY = h / 2;
    const repulsion = 4000;
    const attraction = 0.004;
    const damping = 0.82;
    const centerForce = 0.008;

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    for (const n of nodes) {
      n.vx += (centerX - n.x) * centerForce;
      n.vy += (centerY - n.y) * centerForce;

      for (const m of nodes) {
        if (n.id === m.id) continue;
        const dx = n.x - m.x;
        const dy = n.y - m.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const force = repulsion / (dist * dist);
        n.vx += (dx / dist) * force;
        n.vy += (dy / dist) * force;
      }
    }

    for (const e of edges) {
      const src = nodeMap.get(e.source);
      const tgt = nodeMap.get(e.target);
      if (!src || !tgt) continue;
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      src.vx += dx * attraction;
      src.vy += dy * attraction;
      tgt.vx -= dx * attraction;
      tgt.vy -= dy * attraction;
    }

    for (const n of nodes) {
      if (dragRef.current.node?.id === n.id) continue;
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
    }

    setNodes([...nodes]);
  }, [nodes, edges, canvasSize]);

  // ── Canvas rendering ──────────────────────────────────────────────────────

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || nodes.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio;

    const render = () => {
      simulate();

      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Apply zoom & pan
      ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom, dpr * panOffset.x, dpr * panOffset.y);

      const nodeMap = new Map(nodes.map((n) => [n.id, n]));
      const searchLower = search.toLowerCase();
      const hasSearch = search.length > 0;

      const matchesSearch = (n: GraphNode) =>
        n.name.toLowerCase().includes(searchLower) ||
        n.type.toLowerCase().includes(searchLower);

      // ── Draw edges ────────────────────────────────────────────────
      for (const e of edges) {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) continue;

        const srcVisible = isNodeVisible(src);
        const tgtVisible = isNodeVisible(tgt);
        if (!srcVisible && !tgtVisible) continue;

        const isHovered = hoveredNode && (e.source === hoveredNode || e.target === hoveredNode);
        const isSelected = selectedNode && (e.source === selectedNode.id || e.target === selectedNode.id);
        const isActive = isHovered || isSelected;
        const isDimmed = hasSearch && !matchesSearch(src) && !matchesSearch(tgt);

        // Edge line
        const alpha = isDimmed ? 0.06 : isActive ? 0.7 : 0.18;
        const color = isActive
          ? getTypeColor(src.type).bg
          : `rgba(148, 163, 184, ${alpha})`;

        ctx.strokeStyle = color;
        ctx.lineWidth = isActive ? 2 : 0.8;
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();

        // Arrow head
        if (isActive) {
          const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
          const arrowLen = 8;
          const nodeRadius = 6 + Math.min((connectionCounts.get(tgt.id) || 0) * 0.8, 8);
          const ax = tgt.x - Math.cos(angle) * (nodeRadius + 4);
          const ay = tgt.y - Math.sin(angle) * (nodeRadius + 4);

          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.moveTo(ax, ay);
          ctx.lineTo(ax - arrowLen * Math.cos(angle - 0.35), ay - arrowLen * Math.sin(angle - 0.35));
          ctx.lineTo(ax - arrowLen * Math.cos(angle + 0.35), ay - arrowLen * Math.sin(angle + 0.35));
          ctx.closePath();
          ctx.fill();
        }

        // Relation label on active edges
        if (isActive) {
          const midX = (src.x + tgt.x) / 2;
          const midY = (src.y + tgt.y) / 2;
          ctx.font = "600 9px system-ui, -apple-system, sans-serif";
          ctx.fillStyle = "rgba(203, 213, 225, 0.8)";
          ctx.textAlign = "center";

          // Background pill
          const metrics = ctx.measureText(e.relation);
          const pad = 4;
          ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
          ctx.beginPath();
          const rw = metrics.width + pad * 2;
          const rh = 14;
          const rx = midX - rw / 2;
          const ry = midY - rh / 2 - 1;
          ctx.roundRect(rx, ry, rw, rh, 4);
          ctx.fill();

          ctx.fillStyle = "rgba(203, 213, 225, 0.9)";
          ctx.fillText(e.relation, midX, midY + 3);
        }
      }

      // ── Draw nodes ─────────────────────────────────────────────────
      for (const n of nodes) {
        if (!isNodeVisible(n)) continue;

        const tc = getTypeColor(n.type);
        const connections = connectionCounts.get(n.id) || 0;
        const isHovered = n.id === hoveredNode;
        const isSelected = n.id === selectedNode?.id;
        const isActive = isHovered || isSelected;
        const isDimmed = hasSearch && !matchesSearch(n);

        const baseRadius = 6 + Math.min(connections * 0.8, 8);
        const radius = isActive ? baseRadius + 3 : baseRadius;

        // Outer glow
        if (isActive) {
          const gradient = ctx.createRadialGradient(n.x, n.y, radius, n.x, n.y, radius * 3);
          gradient.addColorStop(0, tc.glow);
          gradient.addColorStop(1, "transparent");
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(n.x, n.y, radius * 3, 0, Math.PI * 2);
          ctx.fill();
        }

        // Search match highlight ring
        if (hasSearch && matchesSearch(n)) {
          ctx.strokeStyle = tc.border;
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.arc(n.x, n.y, radius + 5, 0, Math.PI * 2);
          ctx.stroke();
        }

        // Node fill with gradient
        const nodeGradient = ctx.createRadialGradient(
          n.x - radius * 0.3, n.y - radius * 0.3, 0,
          n.x, n.y, radius
        );
        nodeGradient.addColorStop(0, tc.border);
        nodeGradient.addColorStop(1, tc.bg);

        ctx.fillStyle = isDimmed ? `rgba(100, 116, 139, 0.15)` : nodeGradient;
        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fill();

        // Border ring
        ctx.strokeStyle = isDimmed
          ? "rgba(100, 116, 139, 0.1)"
          : isActive
            ? "#ffffff"
            : `rgba(255, 255, 255, 0.15)`;
        ctx.lineWidth = isActive ? 2 : 0.8;
        ctx.stroke();

        // Label
        if (!isDimmed) {
          const label = n.name.length > 20 ? n.name.slice(0, 18) + "…" : n.name;
          ctx.font = isActive
            ? "600 12px system-ui, -apple-system, sans-serif"
            : "11px system-ui, -apple-system, sans-serif";
          ctx.textAlign = "center";

          // Text shadow
          ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
          ctx.fillText(label, n.x + 1, n.y + radius + 15);

          ctx.fillStyle = isDimmed ? "rgba(148, 163, 184, 0.2)" : "#e2e8f0";
          ctx.fillText(label, n.x, n.y + radius + 14);
        }
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [nodes.length, edges.length, search, hoveredNode, selectedNode, activeFilters, zoom, panOffset, canvasSize]);

  // ── Mouse interactions ────────────────────────────────────────────────────

  const getNodeAt = (sx: number, sy: number): GraphNode | null => {
    const { x, y } = screenToWorld(sx, sy);
    for (const n of [...nodes].reverse()) {
      if (!isNodeVisible(n)) continue;
      const connections = connectionCounts.get(n.id) || 0;
      const radius = 6 + Math.min(connections * 0.8, 8) + 4; // extra hit margin
      const dist = Math.sqrt((n.x - x) ** 2 + (n.y - y) ** 2);
      if (dist < radius) return n;
    }
    return null;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;

    // Panning
    if (isPanningRef.current) {
      const dx = sx - panStartRef.current.x;
      const dy = sy - panStartRef.current.y;
      setPanOffset((prev) => ({ x: prev.x + dx, y: prev.y + dy }));
      panStartRef.current = { x: sx, y: sy };
      return;
    }

    if (dragRef.current.node) {
      const { x, y } = screenToWorld(sx, sy);
      dragRef.current.node.x = x - dragRef.current.offsetX;
      dragRef.current.node.y = y - dragRef.current.offsetY;
      dragRef.current.node.vx = 0;
      dragRef.current.node.vy = 0;
      return;
    }

    const node = getNodeAt(sx, sy);
    setHoveredNode(node?.id || null);
    if (canvasRef.current) {
      canvasRef.current.style.cursor = node ? "pointer" : "grab";
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const node = getNodeAt(sx, sy);

    if (node) {
      const { x, y } = screenToWorld(sx, sy);
      dragRef.current = { node, offsetX: x - node.x, offsetY: y - node.y };
      if (canvasRef.current) canvasRef.current.style.cursor = "grabbing";
    } else {
      // Start panning
      isPanningRef.current = true;
      panStartRef.current = { x: sx, y: sy };
      if (canvasRef.current) canvasRef.current.style.cursor = "grabbing";
    }
  };

  const handleMouseUp = () => {
    dragRef.current = { node: null, offsetX: 0, offsetY: 0 };
    isPanningRef.current = false;
    if (canvasRef.current) canvasRef.current.style.cursor = "grab";
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const node = getNodeAt(sx, sy);
    setSelectedNode(node);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.08 : 1 / 1.08;
    setZoom((z) => Math.max(0.25, Math.min(4, z * factor)));
  };

  const navigateToNode = (nodeName: string) => {
    const target = nodes.find((n) => n.id === nodeName);
    if (target) setSelectedNode(target);
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="px-6 pt-5 pb-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                <Network size={22} className="text-white" />
              </div>
              Knowledge Graph
            </h1>
            <p className="text-sm text-slate-400 mt-1 ml-[52px]">
              Interactive entity relationship visualization
            </p>
          </div>
          <div className="flex gap-2 items-center">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                id="kg-search-input"
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search entities..."
                className="bg-slate-800/60 border border-slate-700/50 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/20 w-56 transition-all"
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                >
                  <X size={12} />
                </button>
              )}
            </div>
            <button
              id="kg-build-button"
              onClick={handleBuild}
              disabled={building}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 rounded-xl text-sm text-white font-medium transition-all disabled:opacity-50 shadow-lg shadow-purple-500/20 hover:shadow-purple-500/30"
            >
              {building ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              {building ? "Building..." : "Build Graph"}
            </button>
          </div>
        </div>
      </div>

      {/* ── Stats Bar ──────────────────────────────────────────────────── */}
      <div className="px-6 py-3 flex gap-3">
        <div className="kg-stat-card rounded-xl px-4 py-3 flex items-center gap-3 min-w-[140px]">
          <div className="w-9 h-9 rounded-lg bg-purple-500/15 flex items-center justify-center">
            <Boxes size={18} className="text-purple-400" />
          </div>
          <div>
            <div className="text-lg font-bold text-white kg-count-up">
              {stats?.nodes ?? "–"}
            </div>
            <div className="text-[11px] text-slate-500 font-medium">Entities</div>
          </div>
        </div>

        <div className="kg-stat-card rounded-xl px-4 py-3 flex items-center gap-3 min-w-[140px]">
          <div className="w-9 h-9 rounded-lg bg-blue-500/15 flex items-center justify-center">
            <GitBranch size={18} className="text-blue-400" />
          </div>
          <div>
            <div className="text-lg font-bold text-white kg-count-up">
              {stats?.edges ?? "–"}
            </div>
            <div className="text-[11px] text-slate-500 font-medium">Relationships</div>
          </div>
        </div>

        <div className="kg-stat-card rounded-xl px-4 py-3 flex items-center gap-3 min-w-[140px]">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/15 flex items-center justify-center">
            <Share2 size={18} className="text-emerald-400" />
          </div>
          <div>
            <div className="text-lg font-bold text-white kg-count-up">
              {entityTypes.size}
            </div>
            <div className="text-[11px] text-slate-500 font-medium">Entity Types</div>
          </div>
        </div>

        {/* Spacer + type filter chips */}
        <div className="flex-1" />
        <div className="flex items-center gap-1.5 flex-wrap">
          <Filter size={13} className="text-slate-500 mr-1" />
          {Array.from(entityTypes.entries()).map(([type, count]) => {
            const tc = getTypeColor(type);
            const isActive = activeFilters.size === 0 || activeFilters.has(type);
            return (
              <button
                key={type}
                onClick={() => toggleFilter(type)}
                className={`kg-type-badge flex items-center gap-1.5 transition-all cursor-pointer ${
                  isActive ? "opacity-100" : "opacity-30"
                }`}
                style={{
                  background: `${tc.bg}22`,
                  color: tc.text,
                  border: `1px solid ${isActive ? tc.bg + "55" : "transparent"}`,
                }}
              >
                <span
                  className="w-2 h-2 rounded-full inline-block"
                  style={{ background: tc.bg }}
                />
                {type}
                <span className="opacity-60">{count}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Build Progress / Result Banner ─────────────────────────────── */}
      {building && (
        <div className="mx-6 mb-2 kg-panel rounded-xl px-5 py-3 flex items-center gap-3 kg-progress-pulse">
          <Loader2 size={16} className="text-purple-400 animate-spin" />
          <div className="flex-1">
            <div className="text-sm text-white font-medium">Building knowledge graph...</div>
            <div className="text-xs text-slate-400 mt-0.5">Extracting entities from document chunks</div>
          </div>
          <div className="h-1.5 w-32 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full kg-shimmer" style={{ width: "60%" }} />
          </div>
        </div>
      )}

      {buildResult && !building && (
        <div className="mx-6 mb-2 kg-panel rounded-xl px-5 py-3 flex items-center justify-between kg-slide-up">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-full bg-emerald-500/15 flex items-center justify-center">
              <span className="text-emerald-400 text-sm">✓</span>
            </div>
            <div>
              <span className="text-sm text-white font-medium">Build complete</span>
              <span className="text-xs text-slate-400 ml-3">
                {buildResult.chunks_processed} chunks → {buildResult.entities_extracted} entities, {buildResult.relationships_extracted} relationships
              </span>
            </div>
          </div>
          <button onClick={() => setBuildResult(null)} className="text-slate-500 hover:text-white transition-colors">
            <X size={14} />
          </button>
        </div>
      )}

      {/* ── Main content area (Graph + Detail Panel) ───────────────────── */}
      <div className="flex-1 flex mx-6 mb-6 gap-4 min-h-0">
        {/* Graph Canvas */}
        <div
          ref={containerRef}
          className="flex-1 relative rounded-2xl overflow-hidden border border-slate-800/80 bg-gradient-to-br from-slate-900/80 to-slate-950/90"
        >
          {/* Subtle grid pattern background */}
          <div
            className="absolute inset-0 opacity-[0.03] pointer-events-none"
            style={{
              backgroundImage: "radial-gradient(circle, #94a3b8 1px, transparent 1px)",
              backgroundSize: "24px 24px",
            }}
          />

          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <Loader2 size={32} className="text-purple-400 animate-spin mb-3" />
              <span className="text-sm text-slate-500">Loading graph data...</span>
            </div>
          ) : nodes.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
              <div className="w-20 h-20 rounded-2xl bg-slate-800/50 flex items-center justify-center mb-5">
                <Network size={36} className="opacity-30" />
              </div>
              <p className="text-base font-medium text-slate-400">No entities yet</p>
              <p className="text-sm mt-1.5 text-slate-500 max-w-xs text-center">
                Upload documents and click <strong>Build Graph</strong> to extract entities and relationships.
              </p>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              width={canvasSize.width}
              height={canvasSize.height}
              style={{ width: "100%", height: "100%", cursor: "grab" }}
              onMouseMove={handleMouseMove}
              onMouseDown={handleMouseDown}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onClick={handleClick}
              onWheel={handleWheel}
            />
          )}

          {/* Zoom Controls */}
          {nodes.length > 0 && (
            <div className="absolute bottom-4 right-4 flex flex-col gap-1.5 kg-slide-up">
              <button
                onClick={handleZoomIn}
                className="w-9 h-9 rounded-lg bg-slate-800/90 border border-slate-700/50 text-slate-400 hover:text-white hover:border-purple-500/40 flex items-center justify-center transition-all"
                title="Zoom in"
              >
                <ZoomIn size={16} />
              </button>
              <button
                onClick={handleZoomOut}
                className="w-9 h-9 rounded-lg bg-slate-800/90 border border-slate-700/50 text-slate-400 hover:text-white hover:border-purple-500/40 flex items-center justify-center transition-all"
                title="Zoom out"
              >
                <ZoomOut size={16} />
              </button>
              <button
                onClick={handleFitView}
                className="w-9 h-9 rounded-lg bg-slate-800/90 border border-slate-700/50 text-slate-400 hover:text-white hover:border-purple-500/40 flex items-center justify-center transition-all"
                title="Fit view"
              >
                <Maximize2 size={16} />
              </button>
            </div>
          )}

          {/* Zoom indicator */}
          {zoom !== 1 && (
            <div className="absolute bottom-4 left-4 text-[10px] text-slate-500 bg-slate-800/80 px-2 py-1 rounded-md font-mono">
              {Math.round(zoom * 100)}%
            </div>
          )}
        </div>

        {/* ── Entity Detail Sidebar ──────────────────────────────────── */}
        {selectedNode && (
          <div className="w-80 kg-panel rounded-2xl p-5 flex flex-col overflow-hidden kg-slide-in shrink-0">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-lg"
                  style={{
                    background: `linear-gradient(135deg, ${getTypeColor(selectedNode.type).bg}, ${getTypeColor(selectedNode.type).border})`,
                    boxShadow: `0 4px 12px ${getTypeColor(selectedNode.type).glow}`,
                  }}
                >
                  <span className="text-white text-lg font-bold">
                    {selectedNode.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-white text-sm truncate">{selectedNode.name}</h3>
                  <span
                    className="kg-type-badge inline-block mt-1"
                    style={{
                      background: `${getTypeColor(selectedNode.type).bg}22`,
                      color: getTypeColor(selectedNode.type).text,
                      border: `1px solid ${getTypeColor(selectedNode.type).bg}44`,
                    }}
                  >
                    {selectedNode.type}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="w-7 h-7 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-500 hover:text-white flex items-center justify-center transition-all shrink-0"
              >
                <X size={14} />
              </button>
            </div>

            {/* Separator */}
            <div className="h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent mb-4" />

            {/* Details */}
            <div className="flex-1 overflow-y-auto space-y-4 text-sm">
              {/* Description */}
              {selectedNode.description && (
                <div>
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Description</span>
                  <p className="text-slate-300 mt-1.5 leading-relaxed text-[13px]">{selectedNode.description}</p>
                </div>
              )}

              {/* Source */}
              {selectedNode.doc_source && (
                <div>
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Source Document</span>
                  <p className="text-slate-400 mt-1.5 text-xs bg-slate-800/60 px-3 py-2 rounded-lg truncate">
                    📄 {selectedNode.doc_source}
                  </p>
                </div>
              )}

              {/* Connection count */}
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Connections</span>
                <p className="text-white mt-1.5 font-medium">
                  {connectionCounts.get(selectedNode.id) || 0} total
                  <span className="text-slate-500 font-normal ml-2">
                    ({selectedNeighbors.outgoing.length} out, {selectedNeighbors.incoming.length} in)
                  </span>
                </p>
              </div>

              {/* Outgoing relationships */}
              {selectedNeighbors.outgoing.length > 0 && (
                <div>
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
                    Outgoing ({selectedNeighbors.outgoing.length})
                  </span>
                  <div className="mt-2 space-y-1.5">
                    {selectedNeighbors.outgoing.map((edge, i) => (
                      <button
                        key={`out-${i}`}
                        onClick={() => navigateToNode(edge.target)}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 transition-all group text-left"
                      >
                        <ArrowRight size={12} className="text-purple-400 shrink-0" />
                        <span className="text-xs text-slate-500 shrink-0">{edge.relation}</span>
                        <span className="text-xs text-slate-300 truncate group-hover:text-white transition-colors">
                          {edge.target}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Incoming relationships */}
              {selectedNeighbors.incoming.length > 0 && (
                <div>
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
                    Incoming ({selectedNeighbors.incoming.length})
                  </span>
                  <div className="mt-2 space-y-1.5">
                    {selectedNeighbors.incoming.map((edge, i) => (
                      <button
                        key={`in-${i}`}
                        onClick={() => navigateToNode(edge.source)}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 transition-all group text-left"
                      >
                        <ArrowRight size={12} className="text-blue-400 shrink-0 rotate-180" />
                        <span className="text-xs text-slate-500 shrink-0">{edge.relation}</span>
                        <span className="text-xs text-slate-300 truncate group-hover:text-white transition-colors">
                          {edge.source}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
