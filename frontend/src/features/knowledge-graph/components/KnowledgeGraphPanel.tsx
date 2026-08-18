import { KnowledgeGraphSidebar } from "./KnowledgeGraphSidebar";
import { KnowledgeGraphStats } from "./KnowledgeGraphStats";


interface Props {
  children: React.ReactNode;
}


export function KnowledgeGraphPanel({
  children,
}: Props) {
  return (
    <div className="flex h-full gap-4">

      <KnowledgeGraphSidebar />

      <main className="flex flex-1 flex-col gap-4">
        {children}

        <KnowledgeGraphStats />
      </main>

    </div>
  );
}