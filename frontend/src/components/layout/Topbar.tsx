import Avatar from "@/components/ui/Avatar";

import {
  Input,
} from "@/components/ui/Input";

import {
  Bell,
  CircleHelp,
} from "lucide-react";


export interface TopbarProps {
  workspaceName?: string;
}

export default function Topbar({
  workspaceName = "AI Resume Intelligence",
}: TopbarProps) {
  return (
    <header
      className="
        flex
        h-16
        items-center
        justify-between
        border-b
        border-slate-200
        bg-white
        px-6
      "
    >
      {/* Left */}
      <div
        className="
          flex
          items-center
          gap-6
        "
      >
        <div>
          <p
            className="
              text-[11px]
              font-medium
              uppercase
              tracking-wider
              text-slate-400
            "
          >
            Workspace
          </p>
          <h1
            className="
              text-sm
              font-semibold
              text-slate-800
            "
          >
            {workspaceName}
          </h1>
        </div>
        <div
          className="
            w-80
          "
        >
          <Input
            placeholder="
              Search resumes, jobs, skills...
            "
          />
        </div>
      </div>
      {/* Right */}
      <div
        className="
          flex
          items-center
          gap-3
        "
      >
        <button
          aria-label="Notifications"
          className="
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-lg
            text-slate-600
            transition-colors
            hover:bg-slate-100
          "
        >
          <Bell size={18} />
        </button>
        <button
          aria-label="Help"
          className="
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-lg
            text-slate-600
            transition-colors
            hover:bg-slate-100
          "
        >
          <CircleHelp size={18} />
        </button>
        <Avatar
          name="Khang"
          size="md"
        />
      </div>
    </header>
  );
}