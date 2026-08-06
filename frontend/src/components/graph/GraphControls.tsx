import type { HTMLAttributes, ReactNode } from "react";

export interface GraphControlsProps
  extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export default function GraphControls({
  children,
  className = "",
  ...props
}: GraphControlsProps) {
  return (
    <div
      className={`
        absolute
        bottom-4
        right-4
        z-20
        flex
        flex-col
        gap-2
        rounded-xl
        border
        border-slate-200
        bg-white
        p-2
        shadow-md
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}