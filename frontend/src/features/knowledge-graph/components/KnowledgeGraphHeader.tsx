import { Search } from "lucide-react";

export function KnowledgeGraphHeader() {
  return (
    <div className="flex items-center justify-between rounded-xl border p-4">
      <div>
        <h1 className="text-xl font-semibold">
          Knowledge Graph
        </h1>

        <p className="text-sm text-muted-foreground">
          Explore relationships between knowledge entities
        </p>
      </div>

      <button
        className="
          flex
          items-center
          gap-2
          rounded-lg
          border
          px-3
          py-2
        "
      >
        <Search size={16} />
        Search
      </button>
    </div>
  );
}