/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { getCandidate } from "./recruitment";
import { ApiError } from "./types";

describe("getCandidate error paths", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should throw ApiError with NETWORK_ERROR when fetch fails", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    vi.stubGlobal("fetch", fetchMock);

    let error: any;
    try {
      await getCandidate("123");
    } catch (e) {
      error = e;
    }

    expect(error).toBeInstanceOf(ApiError);
    expect(error.statusCode).toBe(0);
    expect(error.errorCode).toBe("NETWORK_ERROR");
  });

  it("should throw ApiError with TIMEOUT when fetch is aborted", async () => {
    const domException = new DOMException("The operation was aborted.", "AbortError");
    const fetchMock = vi.fn().mockRejectedValue(domException);
    vi.stubGlobal("fetch", fetchMock);

    let error: any;
    try {
      await getCandidate("123");
    } catch (e) {
      error = e;
    }

    expect(error).toBeInstanceOf(ApiError);
    expect(error.statusCode).toBe(0);
    expect(error.errorCode).toBe("TIMEOUT");
  });

  it("should throw ApiError when response is not ok", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Candidate not found", error_code: "NOT_FOUND" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    let error: any;
    try {
      await getCandidate("123");
    } catch (e) {
      error = e;
    }

    expect(error).toBeInstanceOf(ApiError);
    expect(error.statusCode).toBe(404);
    expect(error.errorCode).toBe("NOT_FOUND");
  });

  it("should return candidate data successfully on 200 OK", async () => {
    const mockData = { id: "123", name: "John Doe" };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getCandidate("123");
    expect(result).toEqual(mockData);
  });
});
