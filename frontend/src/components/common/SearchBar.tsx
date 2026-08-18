import { Search, X } from "lucide-react";
import type { ComponentProps } from "react";

import { Input } from "@/components/ui/Input";

export interface SearchBarProps
  extends Omit<ComponentProps<typeof Input>, "type"> {
  showClearButton?: boolean;
  onClear?: () => void;
}

export default function SearchBar({
  value,
  placeholder = "Search...",
  showClearButton = true,
  onClear,
  className = "",
  ...props
}: SearchBarProps) {
  const hasValue =
    typeof value === "string" && value.length > 0;

  return (
    <div className="relative w-full">
      <Search
        size={18}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
      />

      <Input
        type="text"
        value={value}
        placeholder={placeholder}
        className={`pl-10 pr-10 ${className}`}
        {...props}
      />

      {showClearButton && hasValue && (
        <button
          type="button"
          onClick={onClear}
          aria-label="Clear search"
          className="
            absolute
            right-3
            top-1/2
            -translate-y-1/2
            rounded-md
            p-1
            text-slate-400
            transition-colors
            hover:bg-slate-100
            hover:text-slate-700
          "
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}