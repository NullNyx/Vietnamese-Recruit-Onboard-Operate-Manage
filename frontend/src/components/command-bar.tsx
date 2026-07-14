"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, FileSearch } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { useCurrentUser } from "@/hooks/use-current-user";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { adminNavSection, navItems } from "@/lib/navigation";

interface CommandBarItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

const additionalItems: CommandBarItem[] = [
  { href: "/recruitment/review", label: "Xem xét CV", icon: FileSearch },
  { href: "/recruitment/metrics", label: "Số liệu Pipeline", icon: BarChart3 },
];

interface CommandBarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandBar({ open, onOpenChange }: CommandBarProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);
  const { user } = useCurrentUser();

  useEffect(() => {
    if (open && !wasOpenRef.current) {
      returnFocusRef.current = document.activeElement as HTMLElement | null;
      requestAnimationFrame(() => inputRef.current?.focus());
    }

    if (!open && wasOpenRef.current) {
      requestAnimationFrame(() => returnFocusRef.current?.focus());
    }

    wasOpenRef.current = open;
  }, [open]);

  const allItems: CommandBarItem[] = [
    ...navItems,
    ...additionalItems,
    ...(user?.role === "admin" ? adminNavSection.items : []),
  ];

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <DialogTitle className="sr-only">Tìm kiếm trang</DialogTitle>
      <DialogDescription className="sr-only">
        Tìm và mở nhanh các trang mà bạn có quyền truy cập.
      </DialogDescription>
      <CommandInput
        ref={inputRef}
        placeholder="Tìm kiếm trang..."
        aria-label="Tìm kiếm trang"
      />
      <CommandList>
        <CommandEmpty>Không tìm thấy kết quả</CommandEmpty>
        <CommandGroup heading="Điều hướng">
          {allItems.map((item) => (
            <CommandItem
              key={item.href}
              onSelect={() => {
                router.push(item.href);
                onOpenChange(false);
              }}
            >
              <item.icon className="mr-2 h-4 w-4" aria-hidden="true" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
