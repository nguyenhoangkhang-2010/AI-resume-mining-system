import type {
  FormEvent,
  HTMLAttributes,
} from "react";

interface JobsSearchProps
  extends Omit<
    HTMLAttributes<HTMLFormElement>,
    "onChange"
  > {
  value?: string;

  onChange?: (
    value: string,
  ) => void;

  onSearch?: (
    value: string,
  ) => void;
}

export function JobsSearch({
  value = "",
  onChange,
  onSearch,
  className = "",
  ...props
}: JobsSearchProps) {
  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    onSearch?.(value);
  }

  return (
    <form
      className={`
        flex
        gap-3
        ${className}
      `}
      onSubmit={handleSubmit}
      {...props}
    >
      <input
        value={value}
        onChange={(event) =>
          onChange?.(
            event.target.value,
          )
        }
        placeholder="Search jobs..."
        className="
          h-11
          flex-1
          rounded-xl
          border
          border-slate-200
          bg-white
          px-4
          text-sm
          outline-none
          transition
          focus:border-blue-500
        "
      />

      <button
        type="submit"
        className="
          rounded-xl
          bg-blue-600
          px-5
          text-sm
          font-medium
          text-white
          transition
          hover:bg-blue-700
        "
      >
        Search
      </button>
    </form>
  );
}