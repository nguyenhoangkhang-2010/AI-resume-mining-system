import type {
  HTMLAttributes,
} from "react";

import {
  cn,
} from "@/lib/utils";


export interface DividerProps
  extends HTMLAttributes<HTMLHRElement> {
  orientation?: "horizontal" | "vertical";
}

export default function Divider({
  orientation = "horizontal",
  className,
  ...props
}: DividerProps) {
  const orientationClass =
    orientation === "vertical"
      ? "h-full w-px self-stretch"
      : "h-px w-full";
  return (
    <hr
      className={cn(
        "shrink-0 border-0 bg-slate-200",
        orientationClass,
        className,
      )}
      {...props}
    />
  );
}