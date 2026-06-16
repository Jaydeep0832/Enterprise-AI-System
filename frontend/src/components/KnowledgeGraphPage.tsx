import { useState, useEffect, useRef, useCallback } from "react";
import { Network, Search, Loader2, Play } from "lucide-react";
import api from "../services/api";

type GraphNode = {
  id: string;
  name: string;
  type: string;
  description: string;
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

const TYPE_COLORS: Record<string, string> = {
  PERSON: "#3b82f6",
  ORGANIZATION: "#8b5cf6",
  TECHNOLOGY: "#10b981",
  CONCEPT: "#f59e0b",
  LOCATION: "#ef4444",
  EVENT: "#ec4899",
  unknown: "#64748b",
};

export default function KnowledgeGraphPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number | undefined>(undefined);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [search, setSearch] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [building, setBuilding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const dragRef = useRef<{ node: GraphNode | null; offsetX: number; offsetY: number }>({
    node: null, offsetX: 0, offsetY: 0,
  });

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const [graphRes, statsRes] = await Promise.all([
        api.get("/kg/graph"),
        api.get("/kg/stats"),
      ]);

      const rawNodes = graphRes.data.nodes || [];
      const rawEdges = graphRes.data.edges || [];

      // Initialize positions randomly
      const initialized: GraphNode[] = rawNodes.map((n: any, i: number) => ({
        ...n,
        x: 400 + Math.cos(i * 2.4) * (150 + Math.random() * 200),
        y: 300 + Math.sin(i * 2.4) * (150 + Math.random() * 200),
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
    try {
      await api.post("/kg/build");
      await fetchGraph();
    } catch (err) {
      console.error("Build failed:", err);
    } finally {
      setBuilding(false);
    }
  };

  useEffect(() => { fetchGraph(); }, []);

  // ── Force simulation ──────────────────────────────────────────────────────
  const simulate = useCallback(() => {
    if (nodes.length === 0) return;

    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const centerX = 400, centerY = 300;
    const repulsion = 5000;
    const attraction = 0.005;
    const damping = 0.85;
    const centerForce = 0.01;

    // Apply forces
    for (const n of nodes) {
      // Center gravity
      n.vx += (centerX - n.x) * centerForce;
      n.vy += (centerY - n.y) * centerForce;

      // Node repulsion
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

    // Edge attraction
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

    // Update positions
    for (const n of nodes) {
      if (dragRef.current.node?.id === n.id) continue;
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
    }

    setNodes([...nodes]);
  }, [nodes, edges]);

  // ── Canvas rendering ──────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || nodes.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const render = () => {
      simulate();

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const nodeMap = new Map(nodes.map(n => [n.id, n]));
      const filteredIds = search
        ? new Set(nodes.filter(n =>
            n.name.toLowerCase().includes(search.toLowerCase()) ||
            n.type.toLowerCase().includes(search.toLowerCase())
          ).map(n => n.id))
        : null;

      // Draw edges
      for (const e of edges) {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) continue;

        const isHighlighted = hoveredNode && (e.source === hoveredNode || e.target === hoveredNode);
        const isFiltered = filteredIds && !filteredIds.has(e.source) && !filteredIds.has(e.target);

        ctx.strokeStyle = isHighlighted ? "#3b82f6" : isFiltered ? "rgba(100,116,139,0.1)" : "rgba(100,116,139,0.3)";
        ctx.lineWidth = isHighlighted ? 2 : 1;
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();

        // Draw relation label on highlighted edges
        if (isHighlighted) {
          const midX = (src.x + tgt.x) / 2;
          const midY = (src.y + tgt.y) / 2;
          ctx.font = "10px system-ui";
          ctx.fillStyle = "#94a3b8";
          ctx.textAlign = "center";
          ctx.fillText(e.relation, midX, midY - 5);
        }
      }

      // Draw nodes
      for (const n of nodes) {
        const isHighlighted = n.id === hoveredNode || n.id === selectedNode?.id;
        const isFiltered = filteredIds && !filteredIds.has(n.id);
        const color = TYPE_COLORS[n.type] || TYPE_COLORS.unknown;
        const radius = isHighlighted ? 10 : 7;

        // Glow effect for highlighted
        if (isHighlighted) {
          ctx.shadowColor = color;
          ctx.shadowBlur = 15;
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = isFiltered ? "rgba(100,116,139,0.2)" : color;
        ctx.fill();
        ctx.shadowColor = "transparent";
        ctx.shadowBlur = 0;

        // Border
        ctx.strokeStyle = isHighlighted ? "#ffffff" : "rgba(255,255,255,0.2)";
        ctx.lineWidth = isHighlighted ? 2 : 1;
        ctx.stroke();

        // Label
        if (!isFiltered) {
          ctx.font = isHighlighted ? "bold 12px system-ui" : "11px system-ui";
          ctx.fillStyle = isFiltered ? "rgba(148,163,184,0.3)" : "#e2e8f0";
          ctx.textAlign = "center";
          ctx.fillText(n.name, n.x, n.y + radius + 14);
        }
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [nodes.length, edges.length, search, hoveredNode, selectedNode]);

  // ── Mouse interactions ────────────────────────────────────────────────────
  const getNodeAt = (x: number, y: number): GraphNode | null => {
    for (const n of [...nodes].reverse()) {
      const dist = Math.sqrt((n.x - x) ** 2 + (n.y - y) ** 2);
      if (dist < 12) return n;
    }
    return null;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (dragRef.current.node) {
      dragRef.current.node.x = x - dragRef.current.offsetX;
      dragRef.current.node.y = y - dragRef.current.offsetY;
      dragRef.current.node.vx = 0;
      dragRef.current.node.vy = 0;
      return;
    }

    const node = getNodeAt(x, y);
    setHoveredNode(node?.id || null);
    if (canvasRef.current) {
      canvasRef.current.style.cursor = node ? "pointer" : "default";
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const node = getNodeAt(x, y);
    if (node) {
      dragRef.current = { node, offsetX: x - node.x, offsetY: y - node.y };
    }
  };

  const handleMouseUp = () => {
    dragRef.current = { node: null, offsetX: 0, offsetY: 0 };
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const node = getNodeAt(x, y);
    setSelectedNode(node);
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-6 pb-3 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Network size={28} className="text-purple-400" />
            Knowledge Graph
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {stats ? `${stats.nodes} entities, ${stats.edges} relationships` : "Loading..."}
          </p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search entities..."
              className="bg-slate-800/60 border border-slate-700/50 rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50 w-52"
            />
          </div>
          <button
            onClick={handleBuild}
            disabled={building}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-xl text-sm text-white font-medium transition-colors disabled:opacity-50"
          >
            {building ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Build Graph
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="px-6 pb-3 flex gap-4 flex-wrap">
        {Object.entries(TYPE_COLORS).filter(([k]) => k !== "unknown").map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5 text-xs text-slate-400">
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
            {type}
          </div>
        ))}
      </div>

      {/* Graph Canvas */}
      <div className="flex-1 relative mx-6 mb-6 rounded-2xl overflow-hidden border border-slate-800 bg-slate-900/50">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 size={32} className="text-purple-400 animate-spin" />
          </div>
        ) : nodes.length === 0 ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
            <Network size={48} className="mb-4 opacity-30" />
            <p>No entities in the knowledge graph yet.</p>
            <p className="text-sm mt-1">Upload documents and click "Build Graph" to get started.</p>
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            className="w-full h-full"
            onMouseMove={handleMouseMove}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onClick={handleClick}
          />
        )}

        {/* Selected node details panel */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-72 glass-panel rounded-2xl p-4 shadow-xl">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: TYPE_COLORS[selectedNode.type] || TYPE_COLORS.unknown }} />
                <h3 className="font-semibold text-white text-sm">{selectedNode.name}</h3>
              </div>
              <button onClick={() => setSelectedNode(null)} className="text-slate-500 hover:text-white text-xs">✕</button>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Type</span>
                <span className="text-slate-300">{selectedNode.type}</span>
              </div>
              {selectedNode.description && (
                <div>
                  <span className="text-slate-500">Description</span>
                  <p className="text-slate-300 mt-1">{selectedNode.description}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
