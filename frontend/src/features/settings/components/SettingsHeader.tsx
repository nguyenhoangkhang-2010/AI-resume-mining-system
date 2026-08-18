import type { HTMLAttributes } from "react";

import { PageHeader } from "@/components/common";


export interface SettingsHeaderProps
  extends HTMLAttributes<HTMLDivElement> {}


export function SettingsHeader({
  className = "",
  ...props
}: SettingsHeaderProps) {
  return (
    <PageHeader
      title="Settings"
      description="Manage your profile, preferences, and account security settings."
      className={className}
      {...props}
    />
  );
}