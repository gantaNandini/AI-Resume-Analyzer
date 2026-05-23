import type { HTMLAttributes, ReactNode } from "react";

export type BadgeVariant = "success" | "warning" | "error" | "info" | "default";
export type BadgeSize = "sm" | "md";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  children: ReactNode;
  dot?: boolean;
}

const variantClasses: Record<BadgeVariant, string> = {
  success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
  warning: "bg-amber-500/15 text-amber-400 border-amber-500/25",
  error: "bg-red-500/15 text-red-400 border-red-500/25",
  info: "bg-blue-500/15 text-blue-400 border-blue-500/25",
  default: "bg-white/8 text-slate-300 border-white/12",
};

const dotColors: Record<BadgeVariant, string> = {
  success: "bg-emerald-400",
  warning: "bg-amber-400",
  error: "bg-red-400",
  info: "bg-blue-400",
  default: "bg-slate-400",
};

const sizeClasses: Record<BadgeSize, string> = {
  sm: "text-xs px-2 py-0.5 rounded-md",
  md: "text-sm px-2.5 py-1 rounded-lg",
};

/**
 * Badge component for status indicators and labels.
 * Variants: success (green), warning (amber), error (red), info (blue), default.
 *
 * Requirements: 3.5 (WCAG 2.1 AA contrast)
 */
export function Badge({
  variant = "default",
  size = "sm",
  dot = false,
  children,
  className = "",
  ...props
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 font-medium border",
        variantClasses[variant],
        sizeClasses[size],
        className,
      ].join(" ")}
      {...props}
    >
      {dot && (
        <span
          className={["w-1.5 h-1.5 rounded-full shrink-0", dotColors[variant]].join(" ")}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  );
}
