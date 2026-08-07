import type {
  HTMLAttributes,
} from "react";


import {
  cn,
} from "@/lib/utils";

export interface LogoProps
  extends HTMLAttributes<HTMLDivElement> {

  collapsed?: boolean;

}

export default function Logo({
  collapsed = false,
  className,
  ...props
}: LogoProps) {
  return (
    <div
      className={cn(
        `
        flex
        items-center
        gap-3
        `,
        className,
      )}
      {...props}
    >
      {/* Logo mark */}
      <div
        className="
          flex
          h-10
          w-10
          items-center
          justify-center
          rounded-xl
          bg-white
          text-sm
          font-bold
          text-slate-900
        "
      >
        AI
      </div>
      {/* Brand text */}
      {!collapsed && (
        <div>
          <p
            className="
              text-sm
              font-semibold
              text-white
            "
          >
            Resume AI
          </p>
          <p
            className="
              text-xs
              text-slate-400
            "
          >
            Candidate Matching
          </p>
        </div>
      )}
    </div>
  );
}