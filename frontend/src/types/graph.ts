export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, unknown>;
}


export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
}


export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}