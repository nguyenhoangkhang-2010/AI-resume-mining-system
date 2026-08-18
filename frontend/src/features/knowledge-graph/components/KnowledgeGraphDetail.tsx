interface KnowledgeGraphDetailProps {
  selectedNode?: {
    label: string;
    type: string;
  };
}


export function KnowledgeGraphDetail({
  selectedNode,
}: KnowledgeGraphDetailProps) {
  return (
    <aside
      className="
        w-72
        rounded-xl
        border
        p-4
      "
    >
      <h2 className="mb-4 font-semibold">
        Details
      </h2>

      {selectedNode ? (
        <div className="space-y-2">
          <p className="font-medium">
            {selectedNode.label}
          </p>

          <p className="text-sm text-muted-foreground">
            {selectedNode.type}
          </p>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Select a node to view details
        </p>
      )}
    </aside>
  );
}