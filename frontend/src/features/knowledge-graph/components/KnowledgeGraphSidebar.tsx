export function KnowledgeGraphSidebar() {
  return (
    <aside className="w-64 rounded-xl border p-4">
      <h2 className="mb-4 font-semibold">
        Filters
      </h2>

      <div className="space-y-2 text-sm text-muted-foreground">
        <div>
          All Entities
        </div>

        <div>
          Skills
        </div>

        <div>
          Occupations
        </div>

        <div>
          Certifications
        </div>
      </div>
    </aside>
  );
}