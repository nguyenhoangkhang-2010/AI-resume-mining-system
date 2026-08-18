export function KnowledgeGraphFilter() {
  return (
    <div
      className="
        space-y-3
        rounded-xl
        border
        p-4
      "
    >
      <h3 className="font-semibold">
        Entity Types
      </h3>


      <label className="flex gap-2 text-sm">
        <input type="checkbox" />
        Skills
      </label>


      <label className="flex gap-2 text-sm">
        <input type="checkbox" />
        Occupations
      </label>


      <label className="flex gap-2 text-sm">
        <input type="checkbox" />
        Certifications
      </label>

    </div>
  );
}