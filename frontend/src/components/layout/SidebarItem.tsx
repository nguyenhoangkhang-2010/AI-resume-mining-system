import type {
  ReactNode,
} from "react";

import {
  NavLink,
} from "react-router-dom";


export interface SidebarItemProps {
  icon: ReactNode;
  label: string;
  path: string;
}

export default function SidebarItem({
  icon,
  label,
  path,
}: SidebarItemProps) {
  return (
    <NavLink
      to={path}
      className={({ isActive }) =>
        `
        relative
        flex
        items-center
        gap-3
        rounded-lg
        px-4
        py-2.5
        cursor-pointer
        transition-all
        duration-200
        ${
          isActive
            ? "text-white translate-x-1 bg-white/10"
            : "text-slate-400 hover:text-white hover:bg-white/5"
        }
        `
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span
              className="
              absolute
              left-0
              h-8
              w-1
              rounded-r-full
              bg-white
              "
            />
          )}
          <span
            className="
            flex
            h-5
            w-5
            items-center
            justify-center
            "
          >
            {icon}
          </span>
          <span
            className="
            text-[14px]
            font-medium
            tracking-wide
            "
          >
            {label}
          </span>
        </>
      )}
    </NavLink>
  );
}