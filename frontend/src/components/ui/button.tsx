"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "outline" | "ghost";
type ButtonSize = "default" | "sm" | "icon";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  asChild?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  default:
    "bg-[linear-gradient(135deg,var(--accent),var(--accent2))] text-accent-foreground hover:opacity-95",
  outline:
    "border border-shell-border bg-background text-foreground hover:bg-panel",
  ghost: "text-foreground/72 hover:bg-panel hover:text-foreground",
};

const sizeClasses: Record<ButtonSize, string> = {
  default: "h-10 px-4 text-sm font-medium",
  sm: "h-9 px-3 text-sm font-medium",
  icon: "h-9 w-9 p-0",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "default",
      asChild = false,
      ...props
    },
    ref,
  ) => {
    if (asChild && React.isValidElement(props.children)) {
      const child = props.children as React.ReactElement<{
        className?: string;
      }>;

      return React.cloneElement(child, {
        className: cn(
          "inline-flex items-center justify-center rounded-md transition-colors disabled:cursor-not-allowed disabled:opacity-60",
          variantClasses[variant],
          sizeClasses[size],
          child.props.className,
          className,
        ),
      });
    }

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-md transition-colors disabled:cursor-not-allowed disabled:opacity-60",
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
