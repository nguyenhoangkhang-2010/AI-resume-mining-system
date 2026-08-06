import type { ReactNode } from "react";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import PageContainer from "./PageContainer";

export interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({
  children,
}: AppLayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top navigation */}
        <Topbar />

        {/* Page content */}
        <PageContainer>
          {children}
        </PageContainer>
      </div>
    </div>
  );
}