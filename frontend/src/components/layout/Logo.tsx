import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface LogoProps extends HTMLAttributes<HTMLDivElement> {
  collapsed?: boolean;
}

export default function Logo() {
  return (
    <div className="flex items-center gap-3 px-3">
      <div
        className="
          flex h-9 w-9
          items-center justify-center
          rounded-xl
          bg-white
          text-[#0B1324]
          font-bold
        "
      >
        AI
      </div>

      <div>
        <p className="text-sm font-semibold text-white">
          Resume AI
        </p>

        <p className="text-xs text-slate-400">
          Candidate Matching
        </p>
      </div>
    </div>
  );
}