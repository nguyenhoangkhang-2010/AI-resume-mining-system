import type { HTMLAttributes } from "react";

import { Card } from "@/components/ui";

import type { Settings } from "../types/settings";


export interface SettingsSecurityProps
  extends HTMLAttributes<HTMLDivElement> {
  settings: Settings;
}


export function SettingsSecurity({
  settings,
  className = "",
  ...props
}: SettingsSecurityProps) {
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
          Security
        </h2>

        <p
          className="
            mt-1
            text-sm
            text-slate-500
          "
        >
          Manage account security settings.
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
              Two-factor authentication
            </p>

            <p
              className="
                mt-1
                text-xs
                text-slate-500
              "
            >
              Add an extra layer of account protection.
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
            {settings.twoFactorEnabled
              ? "Enabled"
              : "Disabled"}
          </span>
        </div>


        <button
          type="button"
          className="
            w-fit
            rounded-xl
            bg-slate-900
            px-5
            py-2.5
            text-sm
            font-medium
            text-white
            transition
            hover:bg-slate-800
          "
        >
          Change password
        </button>
      </div>
    </Card>
  );
}