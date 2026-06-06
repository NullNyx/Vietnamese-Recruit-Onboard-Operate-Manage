"use client";

import { useRouter } from "next/navigation";
import { FileSearch, BarChart3 } from "lucide-react";
import { useCurrentUser } from "@/hooks/use-current-user";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { navItems, adminNavSection } from "@/lib/navigation";
import type { LucideIcon } from "lucide-react";

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

  const { user } = useCurrentUser();
  const isAdmin = user?.role === "admin";

  const allItems: CommandBarItem[] = [
    ...navItems,
    ...additionalItems,
    ...(isAdmin ? adminNavSection.items : []),
  ];

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Tìm kiếm trang..." />
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
              <item.icon className="mr-2 h-4 w-4" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
