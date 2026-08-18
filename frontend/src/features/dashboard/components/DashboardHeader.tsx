import { Bell, Search } from "lucide-react";

export function DashboardHeader() {
  return (
    <header
      className="
        flex
        items-center
        justify-between
        gap-6
      "
    >
      <div>
        <h1
          className="
            text-3xl
            font-bold
            tracking-tight
          "
        >
          Dashboard
        </h1>

        <p
          className="
            mt-1
            text-sm
            text-muted-foreground
          "
        >
          Monitor AI recruitment performance and system insights.
        </p>
      </div>

      <div
        className="
          flex
          items-center
          gap-3
        "
      >
        <div
          className="
            flex
            items-center
            gap-2
            rounded-xl
            border
            px-3
            py-2
          "
        >
          <Search size={18} />

          <input
            type="text"
            placeholder="Search..."
            className="
              w-56
              bg-transparent
              outline-none
              text-sm
            "
          />
        </div>

        <button
          className="
            rounded-xl
            border
            p-2
            transition-colors
            hover:bg-muted
          "
        >
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}