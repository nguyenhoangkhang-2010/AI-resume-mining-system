import type { HTMLAttributes, ReactNode } from "react";

export interface GraphToolbarProps
  extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export default function GraphToolbar({
  children,
  className = "",
  ...props
}: GraphToolbarProps) {
  return (
    <div
      className={`flex items-center gap-2 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}