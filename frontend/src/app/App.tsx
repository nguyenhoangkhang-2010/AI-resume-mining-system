import { useEffect, useState } from "react";

import { ConnectionBar } from "../components/ConnectionBar";
import { Icon } from "../components/ui";
import { JobsView } from "../views/JobsView";
import { ResumesView } from "../views/ResumesView";
import { SearchView } from "../views/SearchView";
import { UploadView } from "../views/UploadView";

const TABS = [
  { id: "cv", label: "Read a CV", icon: "upload", view: UploadView },
  { id: "jobs", label: "Jobs", icon: "briefcase", view: JobsView },
  { id: "search", label: "Search", icon: "search", view: SearchView },
  { id: "resumes", label: "Resumes", icon: "files", view: ResumesView },
] as const;

function fromHash(): (typeof TABS)[number]["id"] {
  const id = window.location.hash.replace("#", "");

  return TABS.find((tab) => tab.id === id)?.id ?? "cv";
}

function Brand() {
  return (
    <a className="brand" href="#cv" aria-label="Resume Mining, home">
      <svg viewBox="0 0 32 32" className="brand-mark" aria-hidden="true">
        <rect x="2" y="2" width="28" height="28" rx="8" />
        <path d="M9 11h14M9 16h14M9 21h8" />
        <circle cx="23" cy="21" r="2.4" />
      </svg>
      <span className="brand-name">
        Resume<em>Mining</em>
      </span>
    </a>
  );
}

export default function App() {
  const [tab, setTab] = useState(fromHash);

  useEffect(() => {
    const onChange = () => {
      setTab(fromHash());
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", onChange);

    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const View = TABS.find((entry) => entry.id === tab)!.view;

  return (
    <div className="shell">
      <aside className="side">
        <Brand />

        <nav aria-label="Sections">
          {TABS.map((entry) => (
            <a
              key={entry.id}
              href={`#${entry.id}`}
              aria-current={entry.id === tab ? "page" : undefined}
              className={entry.id === tab ? "tab tab-on" : "tab"}
            >
              <Icon name={entry.icon} />
              {entry.label}
            </a>
          ))}
        </nav>

        <ConnectionBar />
      </aside>

      <main key={tab} className="page">
        <View />
      </main>
    </div>
  );
}
