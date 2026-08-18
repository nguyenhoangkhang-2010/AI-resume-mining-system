import type { FormEvent } from "react";

import { Input, Button } from "@/components/ui";


export interface MatchingSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSearch?: () => void;
}


export function MatchingSearch({
  value,
  onChange,
  onSearch,
}: MatchingSearchProps) {
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
        placeholder="Search candidates, skills, or positions..."
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