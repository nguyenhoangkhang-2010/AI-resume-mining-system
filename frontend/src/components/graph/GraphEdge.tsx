interface GraphEdgeProps {
  label?: string;
}

export function GraphEdge({
  label = "related_to",
}: GraphEdgeProps) {
  return (
    <div
      className="
        absolute
        left-1/2
        top-1/2
        -translate-x-1/2
        -translate-y-1/2
        rounded-full
        bg-background
        px-2
        py-1
        text-xs
        text-muted-foreground
      "
    >
      {label}
    </div>
  );
}