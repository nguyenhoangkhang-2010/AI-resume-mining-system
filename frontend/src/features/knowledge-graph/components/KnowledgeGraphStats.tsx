export function KnowledgeGraphStats() {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="rounded-xl border p-4">
        <p className="text-sm text-muted-foreground">
          Nodes
        </p>

        <p className="text-2xl font-semibold">
          0
        </p>
      </div>


      <div className="rounded-xl border p-4">
        <p className="text-sm text-muted-foreground">
          Relations
        </p>

        <p className="text-2xl font-semibold">
          0
        </p>
      </div>


      <div className="rounded-xl border p-4">
        <p className="text-sm text-muted-foreground">
          Domains
        </p>

        <p className="text-2xl font-semibold">
          0
        </p>
      </div>
    </div>
  );
}