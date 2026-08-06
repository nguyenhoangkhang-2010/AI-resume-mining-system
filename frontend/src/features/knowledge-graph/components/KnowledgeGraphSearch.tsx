import { Search } from "lucide-react";


export function KnowledgeGraphSearch() {
  return (
    <div
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

      <input
        placeholder="Search entities..."
        className="
          flex-1
          bg-transparent
          outline-none
          text-sm
        "
      />
    </div>
  );
}