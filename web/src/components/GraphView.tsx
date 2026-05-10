import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, HelpCircle, ExternalLink, X } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../db';
import HelpModal from './HelpModal';
import type { Note } from '../types';

// ── Types ─────────────────────────────────────────────────────────────────────

interface SimNode {
  id: number;
  title: string;
  x: number; y: number;
  vx: number; vy: number;
  degree: number;
  fixed: boolean;
}

interface Edge { from: number; to: number }

// ── Help ──────────────────────────────────────────────────────────────────────

const HELP_SECTIONS = [
  {
    title: 'Navigation',
    items: [
      { label: 'Glisser (fond)', description: 'Déplacer la vue (pan).' },
      { label: 'Molette / Pincer', description: 'Zoomer et dézoomer.' },
      { label: 'Glisser un nœud', description: 'Repositionner une note manuellement.' },
    ],
  },
  {
    title: 'Interaction',
    items: [
      { label: 'Clic sur un nœud', description: 'Sélectionner la note ; ses connexions se colorent.' },
      { label: 'Bouton Ouvrir', description: 'Ouvrir la note sélectionnée dans l\'éditeur.' },
      { label: 'Clic sur le fond', description: 'Désélectionner.' },
    ],
  },
  {
    title: 'Légende',
    items: [
      { label: 'Nœud indigo (grand)', description: 'Note fortement connectée via des wikilinks.' },
      { label: 'Nœud gris (petit)', description: 'Note isolée, sans wikilink entrant ou sortant.' },
      { label: 'Lignes colorées', description: 'Connexions de la note sélectionnée.' },
    ],
  },
];

// ── Wikilink parser ───────────────────────────────────────────────────────────

function parseTargetIds(
  content: string,
  sourceId: number,
  noteMap: Map<number, unknown>,
  titleMap: Map<string, number>,
): number[] {
  const out: number[] = [];
  // [[Title|id]]
  for (const [, , id] of content.matchAll(/\[\[([^\]|[\n]+)\|(\d+)\]\]/g)) {
    const n = Number(id);
    if (n !== sourceId && noteMap.has(n)) out.push(n);
  }
  // [[Title]] legacy
  for (const [, title] of content.matchAll(/\[\[([^\]|[\n]+)\]\]/g)) {
    const n = titleMap.get(title.toLowerCase());
    if (n !== undefined && n !== sourceId && noteMap.has(n)) out.push(n);
  }
  return out;
}

// ── Props ────────────────────────────────────────────────────────────────────

interface Props {
  onSelectNote: (note: Note) => void;
  onBack: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function GraphView({ onSelectNote, onBack }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  // Simulation state in refs (no re-render per physics step)
  const nodesRef = useRef<SimNode[]>([]);
  const edgesRef = useRef<Edge[]>([]);
  const alphaRef = useRef(1);
  const rafRef   = useRef<number | null>(null);

  // Viewport in refs (imperatively updated) + synced to state for render
  const txRef = useRef(0);
  const tyRef = useRef(0);
  const kRef  = useRef(1);
  const [vp, setVp] = useState({ x: 0, y: 0, k: 1 });

  // Trigger SVG re-render after each physics step
  const [, setTick] = useState(0);

  // UI state
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showHelp, setShowHelp]     = useState(false);

  // Pointer drag state
  const pointerRef = useRef<{
    type: 'pan' | 'node';
    startCX: number; startCY: number;
    panX0?: number;  panY0?: number;
    nodeId?: number;
    moved: boolean;
  } | null>(null);

  // Pinch zoom
  const pinchDistRef = useRef<number | null>(null);

  // ── Data ────────────────────────────────────────────────────────────────────

  const notes = useLiveQuery(() => db.notes.filter(n => !n.is_deleted).toArray()) ?? [];

  useEffect(() => {
    if (!notes.length) return;
    const svg = svgRef.current;
    const W = svg?.clientWidth ?? 600;
    const H = svg?.clientHeight ?? 500;

    const noteMap  = new Map(notes.map(n => [n.id!, n]));
    const titleMap = new Map(notes.map(n => [n.title.toLowerCase(), n.id!]));

    // Build edge list (deduplicated, undirected)
    const edgeSet  = new Set<string>();
    const edges: Edge[] = [];
    const degreeMap = new Map<number, number>();

    for (const note of notes) {
      if (!note.id || !note.content.includes('[[')) continue;
      for (const tid of parseTargetIds(note.content, note.id, noteMap, titleMap)) {
        const key = `${Math.min(note.id, tid)}-${Math.max(note.id, tid)}`;
        if (edgeSet.has(key)) continue;
        edgeSet.add(key);
        edges.push({ from: note.id, to: tid });
        degreeMap.set(note.id, (degreeMap.get(note.id) ?? 0) + 1);
        degreeMap.set(tid,      (degreeMap.get(tid)      ?? 0) + 1);
      }
    }

    // Preserve positions across note updates
    const prevPos = new Map(nodesRef.current.map(n => [n.id, { x: n.x, y: n.y }]));

    nodesRef.current = notes.map(n => {
      const p = prevPos.get(n.id!);
      return {
        id: n.id!,
        title: n.title || 'Sans titre',
        x:  p?.x ?? W / 2 + (Math.random() - 0.5) * W * 0.55,
        y:  p?.y ?? H / 2 + (Math.random() - 0.5) * H * 0.55,
        vx: 0, vy: 0,
        degree: degreeMap.get(n.id!) ?? 0,
        fixed: false,
      };
    });
    edgesRef.current = edges;
    alphaRef.current = 0.9;

    startSim();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notes]);

  // ── Force simulation (Fruchterman-Reingold) ───────────────────────────────

  function startSim() {
    if (rafRef.current !== null) return;

    function tick() {
      const alpha = alphaRef.current;
      if (alpha < 0.002) {
        rafRef.current = null;
        setTick(t => t + 1);
        return;
      }

      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const W = svgRef.current?.clientWidth ?? 600;
      const H = svgRef.current?.clientHeight ?? 500;
      const k = Math.sqrt((W * H) / Math.max(nodes.length, 1)) * 0.88;

      // Repulsion between every pair
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x || 0.01;
          const dy = nodes[j].y - nodes[i].y || 0.01;
          const d  = Math.sqrt(dx * dx + dy * dy);
          const f  = (k * k / d) * alpha;
          const fx = (dx / d) * f, fy = (dy / d) * f;
          nodes[i].vx -= fx; nodes[i].vy -= fy;
          nodes[j].vx += fx; nodes[j].vy += fy;
        }
      }

      // Attraction along edges
      const nmap = new Map(nodes.map(n => [n.id, n]));
      for (const e of edges) {
        const a = nmap.get(e.from), b = nmap.get(e.to);
        if (!a || !b) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const d  = Math.sqrt(dx * dx + dy * dy) || 1;
        const f  = ((d - k) / d) * 0.38 * alpha;
        a.vx += dx * f; a.vy += dy * f;
        b.vx -= dx * f; b.vy -= dy * f;
      }

      // Weak gravity toward canvas center
      for (const n of nodes) {
        n.vx += (W / 2 - n.x) * 0.018 * alpha;
        n.vy += (H / 2 - n.y) * 0.018 * alpha;
      }

      // Integrate + clamp
      for (const n of nodes) {
        if (n.fixed) continue;
        n.vx *= 0.52; n.vy *= 0.52;
        n.x = Math.max(24, Math.min(W - 24, n.x + n.vx));
        n.y = Math.max(24, Math.min(H - 24, n.y + n.vy));
      }

      alphaRef.current *= 0.97;
      setTick(t => t + 1);
      rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);
  }

  // Cancel RAF on unmount
  useEffect(() => () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); }, []);

  // ── Viewport helpers ──────────────────────────────────────────────────────

  function clientToGraph(cx: number, cy: number) {
    const r = svgRef.current!.getBoundingClientRect();
    return {
      x: (cx - r.left - txRef.current) / kRef.current,
      y: (cy - r.top  - tyRef.current) / kRef.current,
    };
  }

  function applyZoom(factor: number, pivotX: number, pivotY: number) {
    kRef.current = Math.max(0.12, Math.min(6, kRef.current * factor));
    txRef.current = pivotX - (pivotX - txRef.current) * factor;
    tyRef.current = pivotY - (pivotY - tyRef.current) * factor;
    setVp({ x: txRef.current, y: tyRef.current, k: kRef.current });
  }

  // ── Pointer events ────────────────────────────────────────────────────────

  function onPointerDown(e: React.PointerEvent<SVGSVGElement>) {
    if (e.button !== 0 && e.pointerType !== 'touch') return;
    svgRef.current!.setPointerCapture(e.pointerId);

    const nodeId = Number((e.target as Element).getAttribute('data-node-id') ?? 0) || null;

    if (nodeId) {
      const node = nodesRef.current.find(n => n.id === nodeId);
      if (node) {
        node.fixed = true;
        alphaRef.current = Math.max(alphaRef.current, 0.3);
        startSim();
      }
      pointerRef.current = { type: 'node', startCX: e.clientX, startCY: e.clientY, nodeId, moved: false };
    } else {
      pointerRef.current = {
        type: 'pan', startCX: e.clientX, startCY: e.clientY,
        panX0: txRef.current, panY0: tyRef.current, moved: false,
      };
    }
  }

  function onPointerMove(e: React.PointerEvent<SVGSVGElement>) {
    const p = pointerRef.current;
    if (!p) return;
    const dx = e.clientX - p.startCX, dy = e.clientY - p.startCY;
    if (dx * dx + dy * dy > 9) p.moved = true;

    if (p.type === 'pan') {
      txRef.current = p.panX0! + dx;
      tyRef.current = p.panY0! + dy;
      setVp({ x: txRef.current, y: tyRef.current, k: kRef.current });
    } else if (p.nodeId) {
      const pos = clientToGraph(e.clientX, e.clientY);
      const node = nodesRef.current.find(n => n.id === p.nodeId);
      if (node) { node.x = pos.x; node.y = pos.y; node.vx = 0; node.vy = 0; }
      setTick(t => t + 1);
    }
  }

  function onPointerUp(_e: React.PointerEvent<SVGSVGElement>) {
    const p = pointerRef.current;
    pointerRef.current = null;
    if (!p) return;

    if (p.type === 'node' && p.nodeId) {
      const node = nodesRef.current.find(n => n.id === p.nodeId);
      if (node) node.fixed = false;
      if (!p.moved) setSelectedId(id => id === p.nodeId ? null : p.nodeId!);
    } else if (p.type === 'pan' && !p.moved) {
      // Click on background → deselect
      setSelectedId(null);
    }
  }

  function onWheel(e: React.WheelEvent<SVGSVGElement>) {
    e.preventDefault();
    const rect = svgRef.current!.getBoundingClientRect();
    applyZoom(e.deltaY < 0 ? 1.12 : 1 / 1.12, e.clientX - rect.left, e.clientY - rect.top);
  }

  function onTouchStart(e: React.TouchEvent) {
    if (e.touches.length === 2) {
      const dx = e.touches[1].clientX - e.touches[0].clientX;
      const dy = e.touches[1].clientY - e.touches[0].clientY;
      pinchDistRef.current = Math.sqrt(dx * dx + dy * dy);
    }
  }

  function onTouchMove(e: React.TouchEvent) {
    if (e.touches.length !== 2 || pinchDistRef.current === null) return;
    const dx   = e.touches[1].clientX - e.touches[0].clientX;
    const dy   = e.touches[1].clientY - e.touches[0].clientY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const rect = svgRef.current!.getBoundingClientRect();
    const mx   = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left;
    const my   = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top;
    applyZoom(dist / pinchDistRef.current, mx, my);
    pinchDistRef.current = dist;
  }

  function onTouchEnd() { pinchDistRef.current = null; }

  // ── Derived selection state ───────────────────────────────────────────────

  const selectedNeighborIds = selectedId !== null
    ? new Set(
        edgesRef.current
          .filter(e => e.from === selectedId || e.to === selectedId)
          .flatMap(e => [e.from, e.to])
      )
    : null;

  const selectedNode = selectedId !== null ? nodesRef.current.find(n => n.id === selectedId) ?? null : null;
  const selectedNote = selectedId !== null ? notes.find(n => n.id === selectedId) ?? null : null;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full bg-gray-950">

      {/* ── Header ── */}
      <div className="flex items-center gap-2 px-4 pt-4 pb-3 border-b border-gray-800 bg-gray-900 shrink-0">
        <button onClick={onBack} className="p-1.5 text-gray-400 active:text-white">
          <ArrowLeft size={22} />
        </button>
        <span className="flex-1 text-sm font-semibold text-gray-200">Vue graphique</span>
        <span className="text-xs text-gray-600 tabular-nums select-none">
          {nodesRef.current.length} notes · {edgesRef.current.length} liens
        </span>
        <button onClick={() => setShowHelp(true)} className="p-1.5 text-gray-500 active:text-gray-200">
          <HelpCircle size={18} />
        </button>
      </div>

      {/* ── SVG Graph ── */}
      <svg
        ref={svgRef}
        className="flex-1 w-full touch-none select-none"
        style={{ cursor: 'grab', background: '#030712' }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onWheel={onWheel}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        <g transform={`translate(${vp.x},${vp.y}) scale(${vp.k})`}>

          {/* Edges */}
          {edgesRef.current.map((edge, i) => {
            const a = nodesRef.current.find(n => n.id === edge.from);
            const b = nodesRef.current.find(n => n.id === edge.to);
            if (!a || !b) return null;
            const lit = selectedNeighborIds?.has(edge.from) && selectedNeighborIds.has(edge.to);
            return (
              <line
                key={i}
                x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke={lit ? '#818CF8' : '#1F2937'}
                strokeWidth={lit ? 1.5 : 1}
                opacity={selectedId !== null ? (lit ? 1 : 0.15) : 0.6}
              />
            );
          })}

          {/* Nodes */}
          {nodesRef.current.map(node => {
            const r          = Math.max(5, Math.min(18, 5 + node.degree * 2.5));
            const isSel      = node.id === selectedId;
            const isNeighbor = !isSel && (selectedNeighborIds?.has(node.id) ?? false);
            const isolated   = node.degree === 0;
            const dimmed     = selectedId !== null && !isSel && !isNeighbor;

            const fill = isSel
              ? '#A5B4FC'
              : isNeighbor
                ? '#818CF8'
                : isolated ? '#374151' : '#6366F1';

            return (
              <g key={node.id} opacity={dimmed ? 0.18 : 1}>
                {/* Selection ring */}
                {isSel && (
                  <circle cx={node.x} cy={node.y} r={r + 5}
                    fill="none" stroke="#A5B4FC" strokeWidth={1.5} opacity={0.5} />
                )}
                {/* Node circle — data-node-id is the hit-test handle */}
                <circle
                  data-node-id={node.id}
                  cx={node.x} cy={node.y} r={r}
                  fill={fill}
                  style={{ cursor: 'pointer' }}
                />
                {/* Label */}
                <text
                  x={node.x} y={node.y + r + 11}
                  textAnchor="middle"
                  fontSize={10}
                  fill={isSel ? '#E0E7FF' : isolated ? '#4B5563' : '#6B7280'}
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {node.title.length > 22 ? node.title.slice(0, 21) + '…' : node.title}
                </text>
              </g>
            );
          })}

          {/* Empty state */}
          {nodesRef.current.length === 0 && (
            <text x="50%" y="50%" textAnchor="middle" fontSize={14} fill="#374151">
              Aucune note à afficher
            </text>
          )}
        </g>
      </svg>

      {/* ── Selected node panel ── */}
      {selectedNode && selectedNote && (
        <div className="bg-gray-900 border-t border-gray-800 px-4 py-3 flex items-center gap-3 shrink-0 safe-bottom">
          <div
            className="w-3 h-3 rounded-full shrink-0"
            style={{ backgroundColor: selectedNode.degree > 0 ? '#6366F1' : '#374151' }}
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-100 truncate">{selectedNode.title}</p>
            <p className="text-xs text-gray-500">
              {selectedNode.degree} lien{selectedNode.degree !== 1 ? 's' : ''}
            </p>
          </div>
          <button
            onClick={() => onSelectNote(selectedNote)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white text-xs font-medium rounded-lg active:bg-indigo-700 shrink-0"
          >
            <ExternalLink size={12} />
            Ouvrir
          </button>
          <button
            onClick={() => setSelectedId(null)}
            className="p-1.5 text-gray-600 active:text-gray-300 shrink-0"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {showHelp && (
        <HelpModal
          title="Aide — Vue graphique"
          sections={HELP_SECTIONS}
          onClose={() => setShowHelp(false)}
        />
      )}
    </div>
  );
}
