import {
  Routes,
  Route,
} from "react-router-dom";


import {
  DashboardPage,
} from "@/features/dashboard";


import {
  ResumesPage,
} from "@/features/resumes";


import {
  JobsPage,
} from "@/features/jobs";


import {
  MatchingPage,
} from "@/features/matching";


import {
  RankingPage,
} from "@/features/ranking";


import {
  RecommendationsPage,
} from "@/features/recommendations";


import {
  KnowledgeGraphPage,
} from "@/features/knowledge-graph";


import {
  VectorSearchPage,
} from "@/features/vector-search";


import {
  AnalyticsPage,
} from "@/features/analytics";


import {
  SettingsPage,
} from "@/features/settings";


import {
  ProtectedRoute,
} from "./ProtectedRoute";

export function AppRoutes() {

  const isAuthenticated = true;


  return (
    <Routes>
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/resumes"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <ResumesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/jobs"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <JobsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/matching"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <MatchingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ranking"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <RankingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recommendations"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <RecommendationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/knowledge-graph"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <KnowledgeGraphPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/vector-search"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <VectorSearchPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <AnalyticsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute
            isAuthenticated={isAuthenticated}
          >
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="*"
        element={<DashboardPage />}
      />
    </Routes>
  );
}