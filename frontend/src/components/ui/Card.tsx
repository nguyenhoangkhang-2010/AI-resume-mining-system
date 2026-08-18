import type {
  HTMLAttributes,
} from "react";

import {
  cn,
} from "@/lib/utils";

export interface CardProps
  extends HTMLAttributes<HTMLDivElement> {}


export default function Card({
  className,
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        `
        rounded-2xl
        border
        border-slate-200
        bg-white
        shadow-sm
        transition-all
        duration-200
        hover:shadow-md
        `,
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-6 pt-6 pb-4",
        className,
      )}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-lg font-semibold text-slate-900",
        className,
      )}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        "mt-1 text-sm text-slate-500",
        className,
      )}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-6 pb-6",
        className,
      )}
      {...props}
    />
  );
}

export function CardFooter({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        `
        flex
        items-center
        justify-end
        gap-2
        border-t
        border-slate-100
        px-6
        py-4
        `,
        className,
      )}
      {...props}
    />
  );
}