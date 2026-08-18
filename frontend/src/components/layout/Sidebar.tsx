import {
  LayoutDashboard,
  FileText,
  Briefcase,
  GitCompare,
  Trophy,
  Network,
  Search,
  BarChart3,
  Sparkles,
  Settings,
} from "lucide-react";

import Logo from "./Logo";
import SidebarItem from "./SidebarItem";


const mainItems = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: <LayoutDashboard size={18} />,
  },
  {
    label: "Resumes",
    path: "/resumes",
    icon: <FileText size={18} />,
  },
  {
    label: "Jobs",
    path: "/jobs",
    icon: <Briefcase size={18} />,
  },
  {
    label: "Matching",
    path: "/matching",
    icon: <GitCompare size={18} />,
  },
  {
    label: "Ranking",
    path: "/ranking",
    icon: <Trophy size={18} />,
  },
  {
    label: "Recommendations",
    path: "/recommendations",
    icon: <Sparkles size={20} />,
  },
  {
    label: "Knowledge Graph",
    path: "/knowledge-graph",
    icon: <Network size={18} />,
  },
  {
    label: "Vector Search",
    path: "/vector-search",
    icon: <Search size={18} />,
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: <BarChart3 size={20} />,
  },
];


export default function Sidebar() {
  return (
    <aside
      className="
      flex
      h-screen
      w-64
      flex-col
      bg-slate-950
      px-4
      py-5
      "
    >
      {/* Logo */}
      <Logo />
      {/* Divider */}
      <div
        className="
        my-5
        h-px
        bg-white/10
        "
      />
      {/* Main navigation */}
      <nav
        className="
        flex
        flex-col
        gap-2
        "
      >
        {mainItems.map((item) => (
          <SidebarItem
            key={item.label}
            {...item}
          />
        ))}
      </nav>
      {/* Bottom settings */}
      <div
        className="
        mt-auto
        "
      >
        <div
          className="
          mb-4
          h-px
          bg-white/10
          "
        />
        <SidebarItem
          label="Settings"
          path="/settings"
          icon={<Settings size={18} />}
        />
      </div>
    </aside>
  );
}