"use client";

import React, { useState, useEffect, useRef } from "react";
import { BACKEND_URL } from "../config";
import { HelpCircle, Network, Info, Award } from "lucide-react";

interface GraphNode {
  id: number;
  name: string;
  type: string;
  description: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphEdge {
  id: number;
  source: number; // node id
  target: number; // node id
  type: string; // BOOSTS, DEPRESSES, SUPPLIES, INFLUENCES, IN_SECTOR, INSTANCE_OF
  strength: number;
  description: string;
}

interface KnowledgeGraphVisualizerProps {
  ticker: string;
}

export default function KnowledgeGraphVisualizer({ ticker }: KnowledgeGraphVisualizerProps) {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Interaction states
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [draggedNodeId, setDraggedNodeId] = useState<number | null>(null);

  const containerRef = useRef<SVGSVGElement | null>(null);
  const requestRef = useRef<number | null>(null);
  
  // Dimensions
  const width = 800;
  const height = 450;

  // Load Graph Data
  useEffect(() => {
    async function fetchGraphData() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${BACKEND_URL}/api/knowledge-graph/asset/${ticker}`);
        if (!res.ok) {
          throw new Error("Failed to fetch graph data");
        }
        const data = await res.json();
        
        // Initialize nodes with random positions near center
        const initializedNodes = data.nodes.map((node: GraphNode) => ({
          ...node,
          x: width / 2 + (Math.random() - 0.5) * 150,
          y: height / 2 + (Math.random() - 0.5) * 150,
          vx: 0,
          vy: 0
        }));

        setNodes(initializedNodes);
        setEdges(data.edges);
      } catch (err: any) {
        setError(err.message || "Something went wrong loading the graph.");
      } finally {
        setLoading(false);
      }
    }
    
    if (ticker) {
      fetchGraphData();
    }
  }, [ticker]);

  // Force-directed layout physics loop
  useEffect(() => {
    if (nodes.length === 0) return;

    let nodesCopy = [...nodes];
    const kRepulsion = 400; // Force pushing nodes apart
    const kAttraction = 0.05; // Spring stiffness pulling nodes together
    const restLength = 100; // Optimal edge length
    const kGravity = 0.02; // Force pulling nodes to center
    const damping = 0.85; // Damping/friction

    const updatePhysics = () => {
      // 1. Repulsion between all node pairs
      for (let i = 0; i < nodesCopy.length; i++) {
        const n1 = nodesCopy[i];
        if (!n1.x || !n1.y) continue;

        for (let j = i + 1; j < nodesCopy.length; j++) {
          const n2 = nodesCopy[j];
          if (!n2.x || !n2.y) continue;

          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const distSq = dx * dx + dy * dy + 0.1; // avoid divide by zero
          const dist = Math.sqrt(distSq);
          
          if (dist < 250) {
            // Force is inversely proportional to distance
            const force = kRepulsion / distSq;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (n1.id !== draggedNodeId) {
              n1.vx = (n1.vx || 0) - fx;
              n1.vy = (n1.vy || 0) - fy;
            }
            if (n2.id !== draggedNodeId) {
              n2.vx = (n2.vx || 0) + fx;
              n2.vy = (n2.vy || 0) + fy;
            }
          }
        }
      }

      // 2. Attraction along edges
      edges.forEach((edge) => {
        const sourceNode = nodesCopy.find((n) => n.id === edge.source);
        const targetNode = nodesCopy.find((n) => n.id === edge.target);

        if (sourceNode && targetNode && sourceNode.x && sourceNode.y && targetNode.x && targetNode.y) {
          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
          
          // Spring force
          const force = kAttraction * (dist - restLength) * (edge.strength || 0.5);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (sourceNode.id !== draggedNodeId) {
            sourceNode.vx = (sourceNode.vx || 0) + fx;
            sourceNode.vy = (sourceNode.vy || 0) + fy;
          }
          if (targetNode.id !== draggedNodeId) {
            targetNode.vx = (targetNode.vx || 0) - fx;
            targetNode.vy = (targetNode.vy || 0) - fy;
          }
        }
      });

      // 3. Gravity pulling toward center
      nodesCopy.forEach((node) => {
        if (node.id === draggedNodeId) return;

        if (node.x && node.y) {
          const dx = width / 2 - node.x;
          const dy = height / 2 - node.y;

          node.vx = (node.vx || 0) + dx * kGravity;
          node.vy = (node.vy || 0) + dy * kGravity;
        }
      });

      // 4. Update positions & damp velocities
      nodesCopy = nodesCopy.map((node) => {
        if (node.id === draggedNodeId) return node;

        const nextX = (node.x || 0) + (node.vx || 0);
        const nextY = (node.y || 0) + (node.vy || 0);

        // Keep inside boundaries
        const padding = 30;
        const boundedX = Math.max(padding, Math.min(width - padding, nextX));
        const boundedY = Math.max(padding, Math.min(height - padding, nextY));

        return {
          ...node,
          x: boundedX,
          y: boundedY,
          vx: (node.vx || 0) * damping,
          vy: (node.vy || 0) * damping
        };
      });

      setNodes(nodesCopy);
      requestRef.current = requestAnimationFrame(updatePhysics);
    };

    requestRef.current = requestAnimationFrame(updatePhysics);
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [nodes.length, edges, draggedNodeId]);

  // Drag handlers
  const handleMouseDown = (nodeId: number) => {
    setDraggedNodeId(nodeId);
    const node = nodes.find((n) => n.id === nodeId);
    if (node) setSelectedNode(node);
    setSelectedEdge(null);
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (draggedNodeId === null || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * width;
    const mouseY = ((e.clientY - rect.top) / rect.height) * height;

    setNodes((prevNodes) =>
      prevNodes.map((n) =>
        n.id === draggedNodeId
          ? { ...n, x: mouseX, y: mouseY, vx: 0, vy: 0 }
          : n
      )
    );
  };

  const handleMouseUpOrLeave = () => {
    setDraggedNodeId(null);
  };

  // Utility to determine node styling based on Entity Type
  const getNodeColor = (type: string, isCenter: boolean) => {
    if (isCenter) return "fill-amber-600 stroke-amber-200 stroke-4 shadow-lg"; // Main asset
    switch (type.toUpperCase()) {
      case "ASSET": return "fill-amber-500 stroke-amber-100 stroke-2";
      case "SECTOR": return "fill-blue-500 stroke-blue-100 stroke-2";
      case "INDICATOR": return "fill-emerald-500 stroke-emerald-100 stroke-2";
      case "ABSTRACT_EVENT": return "fill-rose-500 stroke-rose-100 stroke-2";
      case "EVENT": return "fill-purple-500 stroke-purple-100 stroke-2";
      default: return "fill-zinc-500 stroke-zinc-100 stroke-2";
    }
  };

  const getNodeRadius = (type: string, isCenter: boolean) => {
    if (isCenter) return 22;
    switch (type.toUpperCase()) {
      case "ASSET": return 18;
      case "SECTOR": return 16;
      case "INDICATOR": return 14;
      case "ABSTRACT_EVENT": return 14;
      case "EVENT": return 11;
      default: return 12;
    }
  };

  // Determine edge lines color based on Relationship Type (Multi-Relation support)
  const getEdgeColor = (type: string, isSelected: boolean) => {
    if (isSelected) return "stroke-zinc-900 stroke-3 opacity-100";
    switch (type.toUpperCase()) {
      case "BOOSTS": return "stroke-emerald-500/60 stroke-2 hover:stroke-emerald-600";
      case "DEPRESSES": return "stroke-rose-500/60 stroke-2 hover:stroke-rose-600";
      case "SUPPLIES": return "stroke-amber-500/50 stroke-1.5 hover:stroke-amber-600";
      case "INFLUENCES": return "stroke-blue-500/50 stroke-1.5 hover:stroke-blue-600";
      case "IN_SECTOR": return "stroke-zinc-400/50 stroke-1.5 hover:stroke-zinc-600";
      case "INSTANCE_OF": return "stroke-purple-400/40 stroke-dashed stroke-1 hover:stroke-purple-500";
      default: return "stroke-zinc-300/60 stroke-1 hover:stroke-zinc-450";
    }
  };

  if (loading) {
    return (
      <div className="h-[450px] w-full bg-white/80 border border-[#ebdcb9] rounded-3xl flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-amber-500/20 border-t-amber-600 rounded-full animate-spin"></div>
        <p className="text-xs font-mono text-zinc-500">Compiling multi-relation pathways...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-[450px] w-full bg-white/80 border border-dashed border-rose-500/30 rounded-3xl flex flex-col items-center justify-center space-y-4 p-8 text-center">
        <Network className="w-8 h-8 text-rose-500 opacity-60" />
        <p className="text-xs font-mono text-rose-800 font-bold">[GRAPH_ERROR]: {error}</p>
        <p className="text-[11px] text-zinc-500 max-w-md">Ensure backend is active, database seeded, and the `/api/knowledge-graph/seed` endpoint was invoked on deployment.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
      {/* SVG Canvas Container */}
      <div className="lg:col-span-3 relative bg-[#fdfbf6] border border-[#ebdcb9] rounded-3xl p-4 shadow-inner overflow-hidden select-none">
        
        {/* Graph Legend Overlay */}
        <div className="absolute top-4 left-4 p-3 bg-white/90 backdrop-blur-sm border border-[#ebdcb9] rounded-xl text-[9px] font-mono text-zinc-600 space-y-2 z-10 shadow-sm">
          <p className="font-bold border-b border-[#ebdcb9]/50 pb-1 flex items-center gap-1">
            <Network className="w-3 h-3 text-amber-700" /> LEGEND
          </p>
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 border border-amber-100"></span>
              <span>Asset</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 border border-blue-100"></span>
              <span>Sector</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-emerald-100"></span>
              <span>Indicator</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 border border-rose-100"></span>
              <span>Abstract Event</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500 border border-purple-100"></span>
              <span>Event Instance</span>
            </div>
          </div>
        </div>

        {/* SVG Viewport */}
        <svg
          ref={containerRef}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-[400px] cursor-grab active:cursor-grabbing"
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUpOrLeave}
          onMouseLeave={handleMouseUpOrLeave}
        >
          {/* Defs for arrow markers */}
          <defs>
            <marker id="arrow-boosts" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
            </marker>
            <marker id="arrow-depresses" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e" />
            </marker>
            <marker id="arrow-influences" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
            </marker>
          </defs>

          {/* Render Edges (Paths/Relationships) */}
          {edges.map((edge) => {
            const sourceNode = nodes.find((n) => n.id === edge.source);
            const targetNode = nodes.find((n) => n.id === edge.target);

            if (!sourceNode || !targetNode || !sourceNode.x || !sourceNode.y || !targetNode.x || !targetNode.y) {
              return null;
            }

            const isSelected = selectedEdge?.id === edge.id;
            const arrowMarker = 
              edge.type === "BOOSTS" ? "url(#arrow-boosts)" : 
              edge.type === "DEPRESSES" ? "url(#arrow-depresses)" : 
              edge.type === "INFLUENCES" ? "url(#arrow-influences)" : undefined;

            return (
              <line
                key={edge.id}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                className={`transition-colors duration-200 cursor-pointer ${getEdgeColor(edge.type, isSelected)}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedEdge(edge);
                  setSelectedNode(null);
                }}
                markerEnd={arrowMarker}
              />
            );
          })}

          {/* Render Nodes */}
          {nodes.map((node) => {
            if (!node.x || !node.y) return null;
            const isCenter = node.name === ticker;
            const isSelected = selectedNode?.id === node.id;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                className="cursor-pointer"
                onMouseDown={() => handleMouseDown(node.id)}
              >
                <circle
                  r={getNodeRadius(node.type, isCenter)}
                  className={`transition-all duration-300 ${getNodeColor(node.type, isCenter)} ${
                    isSelected ? "stroke-zinc-950 stroke-3 scale-110" : ""
                  }`}
                />
                
                {/* Node Label Text */}
                <text
                  y={getNodeRadius(node.type, isCenter) + 14}
                  textAnchor="middle"
                  className={`font-mono text-[9px] font-bold fill-zinc-800 ${isCenter ? "fill-amber-900 font-extrabold text-[10px]" : ""}`}
                >
                  {node.name}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Details sidebar panel */}
      <div className="p-5 rounded-3xl bg-white/80 border border-[#ebdcb9] flex flex-col justify-between shadow-sm">
        <div className="space-y-4">
          <div className="flex items-center gap-1.5 border-b border-[#ebdcb9]/60 pb-2.5">
            <Info className="w-4 h-4 text-amber-700" />
            <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-widest font-mono">Entity Inspector</h3>
          </div>

          {selectedNode && (
            <div className="space-y-3 animate-fadeIn">
              <div>
                <span className="px-2 py-0.5 rounded text-[8px] font-mono font-bold bg-amber-500/10 text-amber-800 uppercase border border-amber-500/20">
                  {selectedNode.type}
                </span>
                <h4 className="font-extrabold text-sm text-zinc-950 font-mono mt-1.5">{selectedNode.name}</h4>
              </div>
              <p className="text-[11px] text-zinc-650 leading-relaxed bg-[#fdfbf6] p-3 border border-[#ebdcb9]/40 rounded-xl shadow-inner font-sans">
                {selectedNode.description || "No description provided for this concept."}
              </p>
            </div>
          )}

          {selectedEdge && (
            <div className="space-y-3 animate-fadeIn">
              <div>
                <span className="px-2 py-0.5 rounded text-[8px] font-mono font-bold bg-emerald-500/10 text-emerald-800 uppercase border border-emerald-500/20">
                  RELATION: {selectedEdge.type}
                </span>
                <div className="flex items-center gap-1.5 font-mono text-[10px] font-bold text-zinc-700 mt-2">
                  <span>Strength:</span>
                  <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                    selectedEdge.strength >= 0.7 ? "bg-emerald-100 text-emerald-800" :
                    selectedEdge.strength >= 0.4 ? "bg-amber-100 text-amber-800" : "bg-rose-100 text-rose-800"
                  }`}>
                    {selectedEdge.strength.toFixed(2)}
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-zinc-650 leading-relaxed bg-[#fdfbf6] p-3 border border-[#ebdcb9]/40 rounded-xl shadow-inner font-sans">
                {selectedEdge.description || "Active connection path."}
              </p>
            </div>
          )}

          {!selectedNode && !selectedEdge && (
            <div className="text-center py-12 text-zinc-400 space-y-2">
              <Network className="w-8 h-8 mx-auto opacity-30 animate-pulse text-zinc-650" />
              <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">Select Node or Edge</p>
              <p className="text-[9px] text-zinc-500 leading-relaxed font-sans px-2">
                Click any circles or lines in the graph to inspect connection reasons, strength weights, and descriptions. Drag nodes to reshape layout.
              </p>
            </div>
          )}
        </div>

        {/* Action hint footer */}
        <div className="pt-4 border-t border-zinc-100 flex items-center gap-2 text-[9px] font-mono text-zinc-500">
          <HelpCircle className="w-3.5 h-3.5 text-zinc-400" />
          <span>Interactive consensus mapping loop active.</span>
        </div>
      </div>
    </div>
  );
}
