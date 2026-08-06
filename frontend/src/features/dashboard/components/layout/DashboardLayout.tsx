import type { PropsWithChildren } from "react";

export function DashboardLayout({
  children,
}: PropsWithChildren) {
  return (
    <section
      className="
        flex
        h-full
        flex-col
        gap-6
      "
    >
      {children}
    </section>
  );
}