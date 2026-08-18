import {
  forwardRef,
  type ButtonHTMLAttributes,
  type ReactNode,
} from "react";

import { twMerge } from "tailwind-merge";
import clsx from "clsx";


export type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "danger";


export type ButtonSize =
  | "sm"
  | "md"
  | "lg";

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-blue-600 text-white hover:bg-blue-700 shadow-sm",

  secondary:
    "bg-slate-100 text-slate-900 hover:bg-slate-200",

  outline:
    "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",

  ghost:
    "bg-transparent text-slate-700 hover:bg-slate-100",

  danger:
    "bg-red-600 text-white hover:bg-red-700",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-base",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={twMerge(
          clsx(
            "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200",
            "focus:outline-none focus:ring-2 focus:ring-blue-500",
            "disabled:opacity-60 disabled:pointer-events-none",
            variantClasses[variant],
            sizeClasses[size],
          ),
          className,
        )}
        {...props}
      >
        {loading ? (
          <span
            className="
              h-4
              w-4
              animate-spin
              rounded-full
              border-2
              border-white/40
              border-t-white
            "
          />
        ) : (
          leftIcon
        )}

        {children}

        {!loading && rightIcon}
      </button>
    );
  },
);

Button.displayName = "Button";

export default Button;