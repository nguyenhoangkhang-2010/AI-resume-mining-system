import type { HTMLAttributes } from "react";

export interface JobsFilterOption {
  label: string;
  value: string;
}

interface JobsFilterProps
  extends Omit<
    HTMLAttributes<HTMLDivElement>,
    "onChange"
  > {
  options?: JobsFilterOption[];
  value?: string;
  onChange?: (
    value: string,
  ) => void;
}

export function JobsFilter({
  options = [],
  value = "",
  onChange,
  className = "",
  ...props
}: JobsFilterProps) {
  return (
    <div
      className={`
        flex
        flex-wrap
        gap-3
        ${className}
      `}
      {...props}
    >
      <select
        value={value}
        onChange={(event) =>
          onChange?.(
            event.target.value,
          )
        }
        className="
          h-11
          rounded-xl
          border
          border-slate-200
          bg-white
          px-4
          text-sm
          text-slate-700
          outline-none
          transition
          focus:border-blue-500
        "
      >
        <option value="">
          All filters
        </option>

        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
          >
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}