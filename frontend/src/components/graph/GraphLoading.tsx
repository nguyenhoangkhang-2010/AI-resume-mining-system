import { Loader2 } from "lucide-react";

export default function GraphLoading() {
  return (
    <div className="flex h-full min-h-[320px] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Loader2
          className="h-8 w-8 animate-spin text-slate-400"
        />

        <p className="text-sm text-slate-500">
          Loading graph...
        </p>
      </div>
    </div>
  );
}