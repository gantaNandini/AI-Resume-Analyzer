import { motion } from "framer-motion";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { forwardRef } from "react";
import { Spinner } from "./Spinner";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  children: ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: [
    "bg-gradient-to-r from-primary-600 via-violet-600 to-purple-600",
    "text-white font-semibold",
    "shadow-glow hover:shadow-glow-lg",
    "hover:from-primary-500 hover:via-violet-500 hover:to-purple-500",
    "disabled:from-primary-800 disabled:via-violet-800 disabled:to-purple-800",
    "disabled:shadow-none disabled:opacity-60",
  ].join(" "),

  secondary: [
    "bg-white/10 hover:bg-white/15",
    "text-slate-100 font-medium",
    "border border-white/10 hover:border-white/20",
    "disabled:opacity-50",
  ].join(" "),

  outline: [
    "bg-transparent",
    "text-primary-400 hover:text-primary-300 font-medium",
    "border border-primary-500/50 hover:border-primary-400",
    "hover:bg-primary-500/10",
    "disabled:opacity-50",
  ].join(" "),

  ghost: [
    "bg-transparent hover:bg-white/8",
    "text-slate-300 hover:text-slate-100 font-medium",
    "disabled:opacity-50",
  ].join(" "),
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm rounded-lg gap-1.5",
  md: "h-10 px-5 text-sm rounded-xl gap-2",
  lg: "h-12 px-7 text-base rounded-xl gap-2.5",
};

/**
 * Button component with multiple variants, sizes, and loading state.
 *
 * Requirements: 3.5 (WCAG 2.1 AA contrast)
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      className = "",
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <motion.button
        ref={ref}
        whileHover={isDisabled ? {} : { scale: 1.02 }}
        whileTap={isDisabled ? {} : { scale: 0.98 }}
        transition={{ duration: 0.15 }}
        className={[
          "inline-flex items-center justify-center",
          "transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-dark-950",
          "cursor-pointer disabled:cursor-not-allowed",
          "select-none",
          variantClasses[variant],
          sizeClasses[size],
          className,
        ].join(" ")}
        disabled={isDisabled}
        aria-busy={loading}
        {...(props as React.ComponentProps<typeof motion.button>)}
      >
        {loading ? (
          <>
            <Spinner
              size="sm"
              className={variant === "primary" ? "text-white" : "text-current"}
            />
            <span>{children}</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="shrink-0">{leftIcon}</span>}
            <span>{children}</span>
            {rightIcon && <span className="shrink-0">{rightIcon}</span>}
          </>
        )}
      </motion.button>
    );
  }
);

Button.displayName = "Button";

export { Button };
