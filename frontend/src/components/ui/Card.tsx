import { motion } from "framer-motion";
import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hover?: boolean;
  glass?: boolean;
  gradient?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const paddingMap = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

/**
 * Card component with optional hover animation and glass morphism effect.
 *
 * Requirements: 3.1, 3.2
 */
export function Card({
  children,
  hover = false,
  glass = true,
  gradient = false,
  padding = "md",
  className = "",
  ...props
}: CardProps) {
  const baseClasses = [
    "rounded-2xl",
    "border",
    glass
      ? "bg-white/5 backdrop-blur-xl border-white/10"
      : "bg-dark-800 border-white/8",
    gradient ? "bg-gradient-card" : "",
    paddingMap[padding],
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (hover) {
    return (
      <motion.div
        whileHover={{
          y: -2,
          boxShadow: "0 12px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(99, 102, 241, 0.15)",
          borderColor: "rgba(99, 102, 241, 0.3)",
        }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className={baseClasses}
        {...(props as React.ComponentProps<typeof motion.div>)}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <div className={baseClasses} {...props}>
      {children}
    </div>
  );
}
