import type { HTMLAttributes, ReactNode } from "react";

export interface GraphContainerProps
  extends HTMLAttributes<HTMLDivElement> {
  heading?: ReactNode;
  subtitle?: ReactNode;
  toolbar?: ReactNode;
  children?: ReactNode;
}

export default function GraphContainer({
  title,
  subtitle,
  toolbar,
  children,
  className = "",
  ...props
}: GraphContainerProps) {
  return (
    <section
      className={`
        overflow-hidden
        rounded-2xl
        border
        border-slate-200
        bg-white
        shadow-sm
        ${className}
      `}
      {...props}
    >
      {(title || subtitle || toolbar) && (
        <header className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-slate-900">
                {title}
              </h2>
            )}

            {subtitle && (
              <p className="mt-1 text-sm text-slate-500">
                {subtitle}
              </p>
            )}
          </div>

          {toolbar}
        </header>
      )}

      <div className="h-[500px] w-full">
        {children}
      </div>
    </section>
  );
}