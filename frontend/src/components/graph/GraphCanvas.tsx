import { GraphEdge } from "./GraphEdge";
import { GraphNode } from "./GraphNode";


interface GraphNodeData {
  id: string;
  label: string;
  type: string;
  position: {
    x: string;
    y: string;
  };
}


interface GraphEdgeData {
  id: string;
  from: string;
  to: string;
}


interface GraphCanvasProps {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
}


export function GraphCanvas({
  nodes,
  edges,
}: GraphCanvasProps) {
  return (
    <div
      className="
        relative
        h-full
        min-h-[500px]
        overflow-hidden
        rounded-xl
        border
        bg-muted/20
      "
    >
      {edges.map((edge) => (
        <GraphEdge
          key={edge.id}
          {...edge}
        />
      ))}


      {nodes.map((node) => (
        <GraphNode
          key={node.id}
          label={node.label}
          type={node.type}
          position={node.position}
        />
      ))}
    </div>
  );
}