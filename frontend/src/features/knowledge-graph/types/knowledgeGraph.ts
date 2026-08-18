export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: Record<string, unknown>;
}


export interface KnowledgeGraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
}


export interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}