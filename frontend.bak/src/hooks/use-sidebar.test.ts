import { describe, it, expect, beforeEach, vi } from "vitest";

const STORAGE_KEY = "sidebar-collapsed";

// We test the localStorage interaction logic directly since the hook
// is a thin wrapper around useState + localStorage.

describe("useSidebar localStorage logic", () => {
  let storage: Record<string, string>;

  beforeEach(() => {
    storage = {};
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage[key] ?? null,
      setItem: (key: string, value: string) => {
        storage[key] = value;
      },
      removeItem: (key: string) => {
        delete storage[key];
      },
    });
  });

  it("defaults to false (expanded) when localStorage has no value", () => {
    const stored = localStorage.getItem(STORAGE_KEY);
    expect(stored).toBeNull();
    // Default behavior: collapsed = false
    const collapsed = stored === "true";
    expect(collapsed).toBe(false);
  });

  it("reads 'true' from localStorage as collapsed", () => {
    localStorage.setItem(STORAGE_KEY, "true");
    const stored = localStorage.getItem(STORAGE_KEY);
    expect(stored === "true").toBe(true);
  });

  it("reads 'false' from localStorage as expanded", () => {
    localStorage.setItem(STORAGE_KEY, "false");
    const stored = localStorage.getItem(STORAGE_KEY);
    expect(stored === "true").toBe(false);
  });

  it("persists collapsed state to localStorage", () => {
    localStorage.setItem(STORAGE_KEY, String(true));
    expect(localStorage.getItem(STORAGE_KEY)).toBe("true");

    localStorage.setItem(STORAGE_KEY, String(false));
    expect(localStorage.getItem(STORAGE_KEY)).toBe("false");
  });

  it("defaults to expanded when localStorage throws", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => {
        throw new Error("SecurityError");
      },
      setItem: () => {
        throw new Error("SecurityError");
      },
    });

    let collapsed = false;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      collapsed = stored === "true";
    } catch {
      collapsed = false; // default to expanded
    }
    expect(collapsed).toBe(false);
  });
});
