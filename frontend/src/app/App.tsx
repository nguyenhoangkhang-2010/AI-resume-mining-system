import { useState } from "react";

import AppLayout from "@/components/layout/AppLayout";
import Button from "@/components/ui/Button";

import {
  ErrorState,
  Loading,
  PageContainer,
  PageHeader,
  SearchBar,
} from "@/components/common";

export default function App() {
  const [search, setSearch] = useState("Resume");

  return (
    <AppLayout>
      <PageContainer>
        <PageHeader
          title="Dashboard"
          description="Overview of AI Resume Mining & Candidate Matching System"
          actions={
            <Button>
              Add Resume
            </Button>
          }
        />

        <SearchBar
          value={search}
          placeholder="Search resumes..."
          onChange={(e) => setSearch(e.target.value)}
          onClear={() => setSearch("")}
        />

        <Loading message="Loading dashboard..." />

        <ErrorState
          title="Unable to load data"
          description="Please check your connection and try again."
          action={
            <Button>
              Retry
            </Button>
          }
        />
      </PageContainer>
    </AppLayout>
  );
}