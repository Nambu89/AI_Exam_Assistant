/**
 * Interactive concept-map graph.
 *
 * Runs a d3-force simulation over the GraphRAG-derived nodes/edges and renders
 * it as an accessible SVG. Nodes are coloured by community; dragging repositions
 * a node, clicking selects it. This is the visual differentiator that shows how
 * syllabus concepts connect — something a plain RAG chatbot can't surface.
 */
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import {
  type PointerEvent as ReactPointerEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ConceptEdge, ConceptNode } from "@/types/api";

const WIDTH = 928;
const HEIGHT = 560;

interface SimNode extends SimulationNodeDatum {
  id: string;
  label: string;
  community: number;
  size: number;
}

type SimLink = SimulationLinkDatum<SimNode> & { weight: number };

function communityColor(community: number): string {
  const idx = (Math.abs(community) % 8) + 1;
  return `var(--color-community-${idx})`;
}

function radius(size: number): number {
  return 6 + Math.min(18, Math.sqrt(size) * 3);
}

interface ForceGraphProps {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
  selectedId?: string | null;
  onSelect?: (nodeId: string) => void;
}

export function ForceGraph({ nodes, edges, selectedId, onSelect }: ForceGraphProps) {
  const [, setTick] = useState(0);
  const simRef = useRef<Simulation<SimNode, SimLink> | null>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const dragId = useRef<string | null>(null);

  // Build sim data once per nodes/edges identity.
  const { simNodes, simLinks } = useMemo(() => {
    const ids = new Set(nodes.map((n) => n.id));
    const sn: SimNode[] = nodes.map((n) => ({ ...n }));
    const sl: SimLink[] = edges
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .map((e) => ({ source: e.source, target: e.target, weight: e.weight }));
    return { simNodes: sn, simLinks: sl };
  }, [nodes, edges]);

  useEffect(() => {
    nodesRef.current = simNodes;
    const sim = forceSimulation<SimNode>(simNodes)
      .force(
        "link",
        forceLink<SimNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance(70)
          .strength((l) => Math.min(1, 0.15 + l.weight * 0.08)),
      )
      .force("charge", forceManyBody().strength(-220))
      .force("center", forceCenter(WIDTH / 2, HEIGHT / 2))
      .force(
        "collide",
        forceCollide<SimNode>().radius((d) => radius(d.size) + 6),
      )
      .on("tick", () => setTick((t) => t + 1));

    simRef.current = sim;
    return () => {
      sim.stop();
    };
  }, [simNodes, simLinks]);

  function toLocal(e: ReactPointerEvent<SVGSVGElement>): { x: number; y: number } {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * WIDTH,
      y: ((e.clientY - rect.top) / rect.height) * HEIGHT,
    };
  }

  function onPointerDown(e: ReactPointerEvent<SVGGElement>, id: string) {
    dragId.current = id;
    e.currentTarget.setPointerCapture(e.pointerId);
    simRef.current?.alphaTarget(0.3).restart();
  }

  function onPointerMove(e: ReactPointerEvent<SVGSVGElement>) {
    if (!dragId.current) return;
    const { x, y } = toLocal(e);
    const node = nodesRef.current.find((n) => n.id === dragId.current);
    if (node) {
      node.fx = x;
      node.fy = y;
    }
  }

  function onPointerUp() {
    const node = nodesRef.current.find((n) => n.id === dragId.current);
    if (node) {
      node.fx = null;
      node.fy = null;
    }
    dragId.current = null;
    simRef.current?.alphaTarget(0);
  }

  const linkStroke = "color-mix(in srgb, var(--color-foreground) 18%, transparent)";

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="h-full w-full touch-none"
      role="img"
      aria-label="Concept map of syllabus topics and their relationships"
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}
    >
      <g>
        {simLinks.map((l, i) => {
          const s = l.source as SimNode;
          const t = l.target as SimNode;
          if (typeof s !== "object" || typeof t !== "object") return null;
          return (
            <line
              // biome-ignore lint/suspicious/noArrayIndexKey: links are stable per render set
              key={`l-${i}`}
              x1={s.x ?? 0}
              y1={s.y ?? 0}
              x2={t.x ?? 0}
              y2={t.y ?? 0}
              stroke={linkStroke}
              strokeWidth={Math.min(3, 0.6 + l.weight * 0.3)}
            />
          );
        })}
      </g>
      <g>
        {nodesRef.current.map((n) => {
          const r = radius(n.size);
          const isSelected = n.id === selectedId;
          return (
            // biome-ignore lint/a11y/useSemanticElements: interactive SVG node — a native <button> is not valid inside <svg>
            <g
              key={n.id}
              role="button"
              tabIndex={0}
              aria-label={n.label}
              transform={`translate(${n.x ?? 0}, ${n.y ?? 0})`}
              className="cursor-pointer focus-visible:outline-none"
              onPointerDown={(e) => onPointerDown(e, n.id)}
              onClick={() => onSelect?.(n.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect?.(n.id);
                }
              }}
            >
              <circle
                r={r}
                fill={communityColor(n.community)}
                stroke={isSelected ? "var(--color-foreground)" : "var(--color-card)"}
                strokeWidth={isSelected ? 3 : 1.5}
                opacity={0.92}
              >
                <title>{n.label}</title>
              </circle>
              {r >= 11 && (
                <text
                  y={r + 11}
                  textAnchor="middle"
                  className="pointer-events-none fill-foreground text-[10px] font-medium"
                >
                  {n.label.length > 22 ? `${n.label.slice(0, 21)}…` : n.label}
                </text>
              )}
            </g>
          );
        })}
      </g>
    </svg>
  );
}
