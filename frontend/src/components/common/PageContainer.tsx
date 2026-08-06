import type { HTMLAttributes } from "react";

export interface PageContainerProps
  extends HTMLAttributes<HTMLDivElement> {}

export default function PageContainer({
  children,
  className = "",
  ...props
}: PageContainerProps) {
  return (
    <section
      className={`
        mx-auto
        flex
        w-full
        flex-col
        gap-6
        p-6
        ${className}
      `}
      {...props}
    >
      {children}
    </section>
  );
}