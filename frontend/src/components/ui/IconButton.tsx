import { ButtonHTMLAttributes, ReactNode } from "react";

export interface IconButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "outline" | "ghost";
}

const sizeClasses = {
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-12 w-12",
};

const variantClasses = {
  default:
    "bg-slate-900 text-white hover:bg-slate-800",

  outline:
    "border border-slate-300 bg-white text-slate-700 hover:bg-slate-100",

  ghost:
    "bg-transparent text-slate-700 hover:bg-slate-100",
};

export default function IconButton({
  icon,
  size = "md",
  variant = "ghost",
  className = "",
  disabled,
  ...props
}: IconButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={`
        inline-flex
        items-center
        justify-center
        rounded-lg
        transition-colors
        duration-200
        focus:outline-none
        focus:ring-2
        focus:ring-blue-500
        disabled:cursor-not-allowed
        disabled:opacity-50
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
      {...props}
    >
      {icon}
    </button>
  );
}