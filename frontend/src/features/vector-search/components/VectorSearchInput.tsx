import type { FormEvent } from "react";

import { Button, Input } from "@/components/ui";


export interface VectorSearchInputProps {
  value: string;

  onChange: (value: string) => void;

  onSearch?: () => void;
}


export function VectorSearchInput({
  value,
  onChange,
  onSearch,
}: VectorSearchInputProps) {
  const handleSubmit = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    onSearch?.();
  };


  return (
    <form
      onSubmit={handleSubmit}
      className="
        flex
        flex-col
        gap-3
        sm:flex-row
      "
    >
      <Input
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        placeholder="Search by semantic meaning..."
        className="flex-1"
      />

      <Button
        type="submit"
      >
        Search
      </Button>
    </form>
  );
}