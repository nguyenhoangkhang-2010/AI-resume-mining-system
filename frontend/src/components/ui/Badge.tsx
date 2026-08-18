import type {
  HTMLAttributes,
} from "react";

import {
  cn,
} from "@/lib/utils";


export type BadgeVariant =
  | "default"
  | "secondary"
  | "success"
  | "warning"
  | "danger"
  | "info";
export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantClasses: Record<
  BadgeVariant,
  string
> = {

  default:
    "bg-slate-100 text-slate-700",

  secondary:
    "bg-slate-200 text-slate-600",
  success:
    "bg-emerald-100 text-emerald-700",
  warning:
    "bg-amber-100 text-amber-700",
  danger:
    "bg-red-100 text-red-700",
  info:
    "bg-sky-100 text-sky-700",
};

export default function Badge({
  variant = "default",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        `
        inline-flex
        items-center
        rounded-full
        px-2.5
        py-1
        text-xs
        font-medium
        whitespace-nowrap
        `,
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}