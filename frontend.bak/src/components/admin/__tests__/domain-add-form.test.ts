import { describe, it, expect } from "vitest";
import { domainAddSchema } from "@/lib/api/admin-schemas";

describe("domainAddSchema", () => {
  it("accepts valid domain", () => {
    const result = domainAddSchema.safeParse({ domain: "company.vn" });
    expect(result.success).toBe(true);
  });

  it("accepts subdomain", () => {
    const result = domainAddSchema.safeParse({ domain: "mail.company.vn" });
    expect(result.success).toBe(true);
  });

  it("accepts domain with hyphen", () => {
    const result = domainAddSchema.safeParse({ domain: "my-company.vn" });
    expect(result.success).toBe(true);
  });

  it("rejects domain with @ prefix", () => {
    const result = domainAddSchema.safeParse({ domain: "@company.vn" });
    expect(result.success).toBe(false);
  });

  it("rejects domain with protocol", () => {
    const result = domainAddSchema.safeParse({ domain: "https://company.vn" });
    expect(result.success).toBe(false);
  });

  it("rejects domain starting with hyphen", () => {
    const result = domainAddSchema.safeParse({ domain: "-company.vn" });
    expect(result.success).toBe(false);
  });

  it("rejects empty string", () => {
    const result = domainAddSchema.safeParse({ domain: "" });
    expect(result.success).toBe(false);
  });

  it("rejects single label (no TLD)", () => {
    const result = domainAddSchema.safeParse({ domain: "company" });
    expect(result.success).toBe(false);
  });

  it("rejects too short", () => {
    const result = domainAddSchema.safeParse({ domain: "ab" });
    expect(result.success).toBe(false);
  });

  it("normalizes to lowercase in error message check", () => {
    // The regex requires lowercase, so uppercase should fail
    const result = domainAddSchema.safeParse({ domain: "Company.VN" });
    expect(result.success).toBe(false);
  });
});
