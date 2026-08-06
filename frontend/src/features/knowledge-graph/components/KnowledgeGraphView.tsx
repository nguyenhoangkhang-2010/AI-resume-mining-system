import { GraphContainer } from "@/components/graph";

import { KnowledgeGraphHeader } from "./KnowledgeGraphHeader";
import { KnowledgeGraphLayout } from "./layout/KnowledgeGraphLayout";
import { KnowledgeGraphPanel } from "./KnowledgeGraphPanel";


export function KnowledgeGraphView() {
  return (
    <KnowledgeGraphLayout>

      <KnowledgeGraphHeader />

      <KnowledgeGraphPanel>
        <div className="min-h-0 flex-1">
          <GraphContainer />
        </div>
      </KnowledgeGraphPanel>

    </KnowledgeGraphLayout>
  );
}