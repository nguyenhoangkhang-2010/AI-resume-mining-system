import { HTMLAttributes } from "react";

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  name?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

const sizeClasses = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-14 w-14 text-base",
  xl: "h-20 w-20 text-xl",
};

export default function Avatar({
  src,
  alt,
  name,
  size = "md",
  className = "",
  ...props
}: AvatarProps) {
  const fallback =
    name?.trim().charAt(0).toUpperCase() ?? "?";

  return (
    <div
      className={`
        inline-flex
        items-center
        justify-center
        overflow-hidden
        rounded-full
        bg-slate-200
        text-slate-700
        font-semibold
        select-none
        shrink-0
        ${sizeClasses[size]}
        ${className}
      `}
      {...props}
    >
      {src ? (
        <img
          src={src}
          alt={alt ?? name ?? "Avatar"}
          className="h-full w-full object-cover"
        />
      ) : (
        fallback
      )}
    </div>
  );
}