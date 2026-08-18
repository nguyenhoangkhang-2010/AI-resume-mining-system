export interface RouteConfig {
  path: string;
  label: string;
  protected?: boolean;
}


export const routesConfig: RouteConfig[] = [
  {
    path: "/dashboard",
    label: "Dashboard",
    protected: true,
  },

  {
    path: "/resumes",
    label: "Resumes",
    protected: true,
  },

  {
    path: "/jobs",
    label: "Jobs",
    protected: true,
  },

  {
    path: "/matching",
    label: "Matching",
    protected: true,
  },

  {
    path: "/ranking",
    label: "Ranking",
    protected: true,
  },

  {
    path: "/recommendations",
    label: "Recommendations",
    protected: true,
  },

  {
    path: "/knowledge-graph",
    label: "Knowledge Graph",
    protected: true,
  },

  {
    path: "/vector-search",
    label: "Vector Search",
    protected: true,
  },

  {
    path: "/analytics",
    label: "Analytics",
    protected: true,
  },

  {
    path: "/settings",
    label: "Settings",
    protected: true,
  },
];