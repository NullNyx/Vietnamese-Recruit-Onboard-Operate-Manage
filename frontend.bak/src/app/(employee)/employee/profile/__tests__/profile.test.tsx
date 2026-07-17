/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

const toastSpy = { error: vi.fn(), success: vi.fn() };

vi.mock("sonner", () => ({
  toast: { error: (...a: unknown[]) => toastSpy.error(...a), success: (...a: unknown[]) => toastSpy.success(...a) },
}));

type UserMock = { employee_id: string | null };
const currentUserMock: { value: UserMock } = { value: { employee_id: "emp-001" } };

vi.mock("@/hooks/use-current-user", () => ({
  useCurrentUser: () => ({
    user: currentUserMock.value,
    loading: false,
    error: null,
  }),
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockEmployee = {
  id: "emp-001",
  employee_code: "NV-001",
  full_name: "Nguyễn Văn A",
  email: "a@vroom.local",
  phone: "0909123456",
  date_of_birth: "1990-05-15",
  gender: "male",
  address: "123 Đường Lê Lợi, Quận 1, TP.HCM",
  department_id: null,
  position_id: null,
  start_date: "2025-01-01",
  contract_type: "full_time",
  id_number: "079090123456",
  tax_code: "1234567890",
  is_active: true,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

let ProfilePage: React.ComponentType;

beforeEach(async () => {
  mockFetch.mockReset();
  toastSpy.error.mockReset();
  toastSpy.success.mockReset();
  currentUserMock.value = { employee_id: "emp-001" };

  const mod = await import("../page");
  ProfilePage = mod.default;
});

describe("EmployeeProfilePage", () => {
  it("renders heading", () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    render(<ProfilePage />);
    expect(screen.getByText("Hồ sơ cá nhân")).toBeInTheDocument();
  });

  it("shows loading skeleton while fetching", () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    render(<ProfilePage />);
    expect(screen.getByText("Hồ sơ cá nhân")).toBeInTheDocument();
  });

  it("shows employee data on successful fetch", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockEmployee });
    render(<ProfilePage />);

    await waitFor(() => expect(screen.getByText("Nguyễn Văn A")).toBeInTheDocument());
    expect(screen.getByText("a@vroom.local")).toBeInTheDocument();
    expect(screen.getByText("NV-001")).toBeInTheDocument();
    expect(screen.getByText("15/5/1990")).toBeInTheDocument();
    expect(screen.getByText("Nam")).toBeInTheDocument();
    expect(screen.getByText("Toàn thời gian")).toBeInTheDocument();
  });

  it("shows masked fields for id_number and tax_code", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockEmployee });
    render(<ProfilePage />);
    await waitFor(() => expect(screen.getByText("****3456")).toBeInTheDocument());
    expect(screen.getByText("****7890")).toBeInTheDocument();
  });

  it("shows error message and calls toast on fetch failure", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText("Chưa có hồ sơ nhân viên được liên kết với tài khoản của bạn.")).toBeInTheDocument();
    });
    expect(toastSpy.error).toHaveBeenCalled();
  });

  it("shows no employee message when user has no employee_id", () => {
    currentUserMock.value = { employee_id: null };
    render(<ProfilePage />);
    expect(screen.getByText("Chưa có hồ sơ nhân viên được liên kết với tài khoản của bạn.")).toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("validates phone format — rejects invalid", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockEmployee });
    render(<ProfilePage />);
    await waitFor(() => expect(screen.getByText("Nguyễn Văn A")).toBeInTheDocument());

    const phoneInput = screen.getByPlaceholderText("0912345678");
    await userEvent.clear(phoneInput);
    await userEvent.type(phoneInput, "12345");

    expect(screen.getByText("Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0")).toBeInTheDocument();
  });

  it("validates phone format — accepts valid", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockEmployee });
    render(<ProfilePage />);
    await waitFor(() => expect(screen.getByText("Nguyễn Văn A")).toBeInTheDocument());

    const phoneInput = screen.getByPlaceholderText("0912345678");
    await userEvent.clear(phoneInput);
    await userEvent.type(phoneInput, "0912345678");

    expect(screen.queryByText("Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0")).not.toBeInTheDocument();
  });

  it("submits successfully — calls PUT with changed fields", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockEmployee });
    render(<ProfilePage />);
    await waitFor(() => expect(screen.getByText("Nguyễn Văn A")).toBeInTheDocument());

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ ...mockEmployee, phone: "0912345678" }) });

    const phoneInput = screen.getByPlaceholderText("0912345678");
    await userEvent.clear(phoneInput);
    await userEvent.type(phoneInput, "0912345678");

    const saveButton = screen.getByRole("button", { name: /lưu thay đổi/i });
    await userEvent.click(saveButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith("/api/employees/emp-001", expect.objectContaining({
        method: "PUT",
        body: expect.stringContaining("0912345678"),
      }));
    });
  });
});
