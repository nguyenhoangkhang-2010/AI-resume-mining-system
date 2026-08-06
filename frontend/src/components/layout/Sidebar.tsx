import {
  LayoutDashboard,
  FileText,
  Briefcase,
  GitCompare,
  Trophy,
  Network,
  Search,
  Settings,
} from "lucide-react";

import Logo from "./Logo";
import SidebarItem from "./SidebarItem";


const mainItems = [
  {
    label: "Dashboard",
    icon: <LayoutDashboard size={18} />,
    active: true,
  },
  {
    label: "Resumes",
    icon: <FileText size={18} />,
  },
  {
    label: "Jobs",
    icon: <Briefcase size={18} />,
  },
  {
    label: "Matching",
    icon: <GitCompare size={18} />,
  },
  {
    label: "Ranking",
    icon: <Trophy size={18} />,
  },
  {
    label: "Knowledge Graph",
    icon: <Network size={18} />,
  },
  {
    label: "Vector Search",
    icon: <Search size={18} />,
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
        bg-[#0B1324]
        px-4
        py-5
      "
    >

      {/* Logo */}
      <Logo />


      {/* Divider */}
      <div className="my-5 h-px bg-white/10" />


      {/* Main navigation */}
      <nav className="flex flex-col gap-2">
        {mainItems.map((item) => (
          <SidebarItem
            key={item.label}
            {...item}
          />
        ))}
      </nav>


      {/* Bottom settings */}
      <div className="mt-auto">

        <div className="mb-4 h-px bg-white/10" />

        <SidebarItem
          label="Settings"
          icon={<Settings size={18} />}
        />

      </div>

    </aside>
  );
}