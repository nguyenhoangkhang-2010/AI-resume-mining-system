import type { FormEvent } from "react";

import { Button, Input } from "@/components/ui";


export interface RankingSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSearch?: () => void;
}


export function RankingSearch({
  value,
  onChange,
  onSearch,
}: RankingSearchProps) {
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
        placeholder="Search candidates, positions, or rankings..."
        className="flex-1"
      />

      <Button type="submit">
        Search
      </Button>
    </form>
  );
}