interface GraphNodeProps {
  label: string;
  type: string;
  position: {
    x: string;
    y: string;
  };
}


export function GraphNode({
  label,
  type,
  position,
}: GraphNodeProps) {
  return (
    <div
      className="
        absolute
        rounded-xl
        border
        bg-background
        px-4
        py-3
        shadow-sm
      "
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <p className="font-medium">
        {label}
      </p>

      <p className="
        text-xs
        text-muted-foreground
      ">
        {type}
      </p>
    </div>
  );
}