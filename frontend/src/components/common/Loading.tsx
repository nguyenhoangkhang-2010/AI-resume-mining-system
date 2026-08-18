import type { HTMLAttributes } from "react";

export interface LoadingProps
  extends HTMLAttributes<HTMLDivElement> {
  message?: string;
  size?: "sm" | "md" | "lg";
  fullPage?: boolean;
}

const spinnerSize = {
  sm: "h-5 w-5 border-2",
  md: "h-8 w-8 border-[3px]",
  lg: "h-12 w-12 border-4",
};

export default function Loading({
  message = "Loading...",
  size = "md",
  fullPage = false,
  className = "",
  ...props
}: LoadingProps) {
  return (
    <div
      className={`
        flex
        flex-col
        items-center
        justify-center
        gap-4
        ${fullPage ? "h-full min-h-screen" : "py-10"}
        ${className}
      `}
      {...props}
    >
      <div
        className={`
          animate-spin
          rounded-full
          border-slate-300
          border-t-sky-600
          ${spinnerSize[size]}
        `}
      />

      {message && (
        <p className="text-sm text-slate-500">
          {message}
        </p>
      )}
    </div>
  );
}