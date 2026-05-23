import type { HTMLAttributes } from "react";

export type SpinnerSize = "xs" | "sm" | "md" | "lg" | "xl";

interface SpinnerProps extends HTMLAttributes<SVGElement> {
  size?: SpinnerSize;
}

const sizeMap: Record<SpinnerSize, string> = {
  xs: "w-3 h-3",
  sm: "w-4 h-4",
  md: "w-6 h-6",
  lg: "w-8 h-8",
  xl: "w-12 h-12",
};

/**
 * Animated loading spinner using an SVG circle stroke animation.
 * Accessible: includes role="status" and a visually-hidden label.
 */
export function Spinner({ size = "md", className = "", ...props }: SpinnerProps) {
  return (
    <svg
      role="status"
      aria-label="Loading"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={[
        sizeMap[size],
        "animate-spin",
        "text-primary-400",
        className,
      ].join(" ")}
      {...props}
    >
      {/* Track */}
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeOpacity="0.2"
      />
      {/* Spinning arc */}
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
