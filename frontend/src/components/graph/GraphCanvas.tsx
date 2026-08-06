import type { HTMLAttributes, ReactNode } from "react";

export interface GraphCanvasProps
  extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export default function GraphCanvas({
  children,
  className = "",
  ...props
}: GraphCanvasProps) {
  return (
    <div
      className={`relative h-full w-full overflow-hidden bg-slate-50 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}