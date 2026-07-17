import { describe, it, expect } from "vitest";

describe("MegaMenuPanel component module", () => {
  it("exports MegaMenuPanel as a function", async () => {
    const mod = await import("./mega-menu-panel");
    expect(typeof mod.MegaMenuPanel).toBe("function");
  });

  it("module can be imported without errors", async () => {
    const mod = await import("./mega-menu-panel");
    expect(mod).toHaveProperty("MegaMenuPanel");
  });
});
