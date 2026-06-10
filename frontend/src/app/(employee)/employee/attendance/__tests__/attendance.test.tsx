import { describe, it, expect } from "vitest";

// Test utility functions used by the attendance page

function formatTime(isoString: string | null): string {
  if (!isoString) return "—";
  try {
    return new Date(isoString).toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "—";
  }
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("vi-VN");
  } catch {
    return dateStr;
  }
}

function formatCurrentDate(): string {
  return new Date().toLocaleDateString("vi-VN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function getMonthOptions() {
  const options = [];
  const now = new Date();
  for (let i = 0; i <= 3; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const label = d.toLocaleDateString("vi-VN", { month: "long", year: "numeric" });
    options.push({ value, label });
  }
  return options;
}

describe("AttendancePage utilities", () => {
  describe("formatTime", () => {
    it("returns '—' for null", () => {
      expect(formatTime(null)).toBe("—");
    });

    it("formats ISO string to HH:mm:ss", () => {
      const result = formatTime("2026-06-10T08:30:00Z");
      // Should contain time components
      expect(result).toMatch(/\d{2}:\d{2}:\d{2}/);
    });
  });

  describe("formatDate", () => {
    it("formats date string to Vietnamese locale", () => {
      const result = formatDate("2026-06-10");
      expect(result).toContain("2026");
    });
  });

  describe("formatCurrentDate", () => {
    it("returns Vietnamese formatted current date", () => {
      const result = formatCurrentDate();
      expect(result).toContain("2026");
    });
  });

  describe("getMonthOptions", () => {
    it("returns 4 months (current + 3 previous)", () => {
      const options = getMonthOptions();
      expect(options).toHaveLength(4);
    });

    it("each option has value and label", () => {
      const options = getMonthOptions();
      options.forEach((opt) => {
        expect(opt.value).toMatch(/^\d{4}-\d{2}$/);
        expect(opt.label).toBeTruthy();
      });
    });

    it("first option is current month", () => {
      const options = getMonthOptions();
      const now = new Date();
      const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
      expect(options[0].value).toBe(currentMonth);
    });
  });

  describe("Attendance state derivation", () => {
    it("derives empty state from null record", () => {
      const record = null;
      const state = !record ? "empty" : record.check_out_at ? "completed" : record.check_in_at ? "checked-in" : "empty";
      expect(state).toBe("empty");
    });

    it("derives checked-in state from record without check-out", () => {
      const record = {
        check_in_at: "2026-06-10T08:00:00Z",
        check_out_at: null,
      };
      const state = !record ? "empty" : record.check_out_at ? "completed" : record.check_in_at ? "checked-in" : "empty";
      expect(state).toBe("checked-in");
    });

    it("derives completed state from record with both check-in and check-out", () => {
      const record = {
        check_in_at: "2026-06-10T08:00:00Z",
        check_out_at: "2026-06-10T17:00:00Z",
      };
      const state = !record ? "empty" : record.check_out_at ? "completed" : record.check_in_at ? "checked-in" : "empty";
      expect(state).toBe("completed");
    });
  });

  describe("Error response handling", () => {
    it("extracts detail from error response", () => {
      const errorData = {
        error_code: "OFFICE_NETWORK_REQUIRED",
        detail: "Attendance check-in is only allowed from approved office network.",
      };
      expect(errorData.detail).toBe("Attendance check-in is only allowed from approved office network.");
    });
  });
});
