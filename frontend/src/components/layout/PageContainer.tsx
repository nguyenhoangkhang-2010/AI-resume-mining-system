import type {
  HTMLAttributes,
} from "react";


import {
  cn,
} from "@/lib/utils";

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
        `
        flex-1
        overflow-auto
        bg-slate-50
        px-6
        py-6
        lg:px-8
        scrollbar-thin
        scrollbar-thumb-slate-300
        `,
        className,
      )}
      {...props}
    >
      {children}
    </main>
  );
}