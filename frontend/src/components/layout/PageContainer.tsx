import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface PageContainerProps
  extends HTMLAttributes<HTMLDivElement> {}

export default function PageContainer({
  className,
  children,
  ...props
}: PageContainerProps) {
  return (
    <main
      className={cn(
        "flex-1 overflow-auto bg-slate-50 p-6",
        className
      )}
      {...props}
    >
      {children}
    </main>
  );
}