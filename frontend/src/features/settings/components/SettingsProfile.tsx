import type { HTMLAttributes } from "react";

import { Card } from "@/components/ui";

import type { Settings } from "../types/settings";


export interface SettingsProfileProps
  extends HTMLAttributes<HTMLDivElement> {
  settings: Settings;
}


export function SettingsProfile({
  settings,
  className = "",
  ...props
}: SettingsProfileProps) {
  return (
    <Card
      className={`
        flex
        flex-col
        gap-6
        p-6
        ${className}
      `}
      {...props}
    >
      <div>
        <h2
          className="
            text-lg
            font-semibold
            text-slate-900
          "
        >
          Profile Information
        </h2>

        <p
          className="
            mt-1
            text-sm
            text-slate-500
          "
        >
          Manage your account profile details.
        </p>
      </div>


      <div
        className="
          grid
          grid-cols-1
          gap-4
          md:grid-cols-2
        "
      >
        <div>
          <p
            className="
              text-xs
              font-medium
              uppercase
              tracking-wide
              text-slate-400
            "
          >
            Name
          </p>

          <p
            className="
              mt-2
              text-sm
              font-medium
              text-slate-900
            "
          >
            {settings.name}
          </p>
        </div>


        <div>
          <p
            className="
              text-xs
              font-medium
              uppercase
              tracking-wide
              text-slate-400
            "
          >
            Email
          </p>

          <p
            className="
              mt-2
              text-sm
              font-medium
              text-slate-900
            "
          >
            {settings.email}
          </p>
        </div>
      </div>
    </Card>
  );
}