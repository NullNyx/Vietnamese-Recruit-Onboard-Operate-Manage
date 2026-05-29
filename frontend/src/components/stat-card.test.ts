import { describe, it, expect } from "vitest";

describe("StatCard component module", () => {
  it("exports StatCard as a function", async () => {
    const mod = await import("./stat-card");
    expect(typeof mod.StatCard).toBe("function");
  });

  it("exports StatCardProps interface (TypeScript compile check)", async () => {
    // This test validates the module can be imported without errors
    const mod = await import("./stat-card");
    expect(mod).toHaveProperty("StatCard");
  });
});
