import type { HTMLAttributes } from "react";

import { Card } from "@/components/ui";

import type { Settings } from "../types/settings";


export interface SettingsPreferencesProps
  extends HTMLAttributes<HTMLDivElement> {
  settings: Settings;
}


export function SettingsPreferences({
  settings,
  className = "",
  ...props
}: SettingsPreferencesProps) {
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
          Preferences
        </h2>

        <p
          className="
            mt-1
            text-sm
            text-slate-500
          "
        >
          Configure your application preferences.
        </p>
      </div>


      <div
        className="
          flex
          flex-col
          gap-4
        "
      >
        <div
          className="
            flex
            items-center
            justify-between
            rounded-xl
            border
            border-slate-200
            p-4
          "
        >
          <div>
            <p
              className="
                text-sm
                font-medium
                text-slate-900
              "
            >
              Notifications
            </p>

            <p
              className="
                mt-1
                text-xs
                text-slate-500
              "
            >
              Receive updates and system alerts.
            </p>
          </div>

          <span
            className="
              rounded-full
              bg-slate-100
              px-3
              py-1
              text-xs
              font-medium
              text-slate-700
            "
          >
            {settings.notifications
              ? "Enabled"
              : "Disabled"}
          </span>
        </div>


        <div
          className="
            flex
            items-center
            justify-between
            rounded-xl
            border
            border-slate-200
            p-4
          "
        >
          <div>
            <p
              className="
                text-sm
                font-medium
                text-slate-900
              "
            >
              Language
            </p>

            <p
              className="
                mt-1
                text-xs
                text-slate-500
              "
            >
              Current application language.
            </p>
          </div>

          <span
            className="
              rounded-full
              bg-slate-100
              px-3
              py-1
              text-xs
              font-medium
              text-slate-700
            "
          >
            {settings.language}
          </span>
        </div>
      </div>
    </Card>
  );
}