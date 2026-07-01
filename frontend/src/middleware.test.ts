import { describe, it, expect } from "vitest";
import { middleware } from "./middleware";
import { NextRequest } from "next/server";

function createMockRequest(
  path: string,
  cookies: Record<string, string> = {},
): NextRequest {
  const url = new URL(path, "http://localhost:3000");
  const request = new NextRequest(url);
  for (const [name, value] of Object.entries(cookies)) {
    request.cookies.set(name, value);
  }
  return request;
}

describe("middleware", () => {
  describe("setup routes", () => {
    it("allows /setup without token (backend status check fails-safe)", async () => {
      const request = createMockRequest("/setup");
      const response = await middleware(request);
      // No backend → catch returns next() → 200
      expect(response.status).toBe(200);
    });

    it("allows /setup/administrator without token", async () => {
      const request = createMockRequest("/setup/administrator");
      const response = await middleware(request);
      expect(response.status).toBe(200);
    });
  });

  describe("admin dashboard route protection", () => {
    it("redirects to /login when no access_token on admin routes", async () => {
      const request = createMockRequest("/admin/users");
      const response = await middleware(request);

      expect(response.status).toBe(307);
      expect(response.headers.get("location")).toBe(
        "http://localhost:3000/login",
      );
    });

    it("allows request through when access_token exists", async () => {
      const request = createMockRequest("/admin/users", {
        access_token: "some-valid-token",
      });
      const response = await middleware(request);

      expect(response.status).toBe(200);
      expect(response.headers.get("location")).toBeNull();
    });
  });

  describe("general route protection", () => {
    it("redirects to /login when no access_token on unmatched routes", async () => {
      const request = createMockRequest("/some-other-page");
      const response = await middleware(request);

      expect(response.status).toBe(307);
      expect(response.headers.get("location")).toBe(
        "http://localhost:3000/login",
      );
    });

    it("allows request through when access_token exists", async () => {
      const request = createMockRequest("/some-other-page", {
        access_token: "some-valid-token",
      });
      const response = await middleware(request);

      expect(response.status).toBe(200);
      expect(response.headers.get("location")).toBeNull();
    });
  });
});
