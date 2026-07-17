"use client";

import { motion } from "motion/react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NavGroup } from "@/lib/header-nav-config";

interface NavItemTriggerProps {
  group: NavGroup;
  isActive: boolean;
  isOpen: boolean;
  onToggle: () => void;
}

export function NavItemTrigger({
  group,
  isActive,
  isOpen,
  onToggle,
}: NavItemTriggerProps): JSX.Element {
  const Icon = group.icon;

  return (
    <button
      type="button"
      className={cn(
        "relative inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors",
        "rounded-md hover:bg-foreground/8 hover:text-accent-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        isActive && "text-primary font-semibold",
        // Gradient underline for active indicator (replaces solid primary)
        isActive &&
          "after:absolute after:bottom-0 after:left-2 after:right-2 after:h-0.5 after:bg-gradient-to-r after:from-primary/80 after:to-primary after:rounded-full",
        isOpen && "bg-accent/10 text-accent-foreground",
      )}
      aria-expanded={isOpen}
      aria-haspopup="true"
      onClick={onToggle}
    >
      {Icon && <Icon className="size-4" aria-hidden="true" />}
      <span>{group.label}</span>
      {/* Animated chevron */}
      <motion.span
        aria-hidden="true"
        className="inline-flex"
        animate={{ rotate: isOpen ? 180 : 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      >
        <ChevronDown className="size-3.5 text-muted-foreground" />
      </motion.span>
    </button>
  );
}
