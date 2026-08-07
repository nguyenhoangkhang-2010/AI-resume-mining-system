import {
  SettingsHeader,
  SettingsPreferences,
  SettingsProfile,
  SettingsSecurity,
} from "..";

import { useSettings } from "../hooks/useSettings";
import { useState } from "react";


export function SettingsView() {
  const {
    loading,
    error,
    settings,
  } = useSettings();

  const [activeSection, setActiveSection] =
    useState("profile");


  if (loading) {
    return (
      <div>
        Loading settings...
      </div>
    );
  }


  if (error) {
    return (
      <div>
        Failed to load settings
      </div>
    );
  }


  return (
    <section
      className="
        flex
        flex-col
        gap-6
      "
    >
      <SettingsHeader />

      <div
        className="
          grid
          grid-cols-1
          gap-6
          lg:grid-cols-[220px_1fr]
        "
      >
        <nav
          className="
            flex
            flex-col
            gap-1
            rounded-2xl
            border
            border-slate-200
            bg-white
            p-2
            shadow-sm
          "
        >
          <button
            type="button"
            onClick={() =>
              setActiveSection("profile")
            }
            className={`
              rounded-xl
              px-4
              py-3
              text-left
              text-sm
              font-medium
              transition-colors
              ${
                activeSection === "profile"
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-500 hover:bg-slate-50"
              }
            `}
          >
            Profile
          </button>

          <button
            type="button"
            onClick={() =>
              setActiveSection("preferences")
            }
            className={`
              rounded-xl
              px-4
              py-3
              text-left
              text-sm
              font-medium
              transition-colors
              ${
                activeSection === "preferences"
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-500 hover:bg-slate-50"
              }
            `}
          >
            Preferences
          </button>

          <button
            type="button"
            onClick={() =>
              setActiveSection("security")
            }
            className={`
              rounded-xl
              px-4
              py-3
              text-left
              text-sm
              font-medium
              transition-colors
              ${
                activeSection === "security"
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-500 hover:bg-slate-50"
              }
            `}
          >
            Security
          </button>
        </nav>

        <div className="min-w-0">
          {settings ? (
            <>
                {activeSection === "profile" && (
                <SettingsProfile
                    settings={settings}
                />
                )}

                {activeSection === "preferences" && (
                <SettingsPreferences
                    settings={settings}
                />
                )}

                {activeSection === "security" && (
                <SettingsSecurity
                    settings={settings}
                />
                )}
            </>
            ) : (
            <div
                className="
                rounded-2xl
                border
                border-slate-200
                bg-white
                p-6
                text-sm
                text-slate-500
                "
            >
                No settings available.
            </div>
            )}
        </div>
      </div>
    </section>
  );
}