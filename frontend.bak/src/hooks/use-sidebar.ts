"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "sidebar-collapsed";

function getStoredValue(): boolean {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "true") return true;
    if (stored === "false") return false;
    return false; // default to expanded
  } catch {
    // localStorage unavailable (SSR or error)
    return false;
  }
}

export function useSidebar() {
  const [collapsed, setCollapsedState] = useState<boolean>(false);

  // Sync from localStorage on mount to avoid SSR mismatch
  useEffect(() => {
    setCollapsedState(getStoredValue());
  }, []);

  const setCollapsed = useCallback((value: boolean) => {
    setCollapsedState(value);
    try {
      localStorage.setItem(STORAGE_KEY, String(value));
    } catch {
      // localStorage unavailable — silently ignore
    }
  }, []);

  const toggle = useCallback(() => {
    setCollapsed(!collapsed);
  }, [collapsed, setCollapsed]);

  return { collapsed, toggle, setCollapsed };
}
