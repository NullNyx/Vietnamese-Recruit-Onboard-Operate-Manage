/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const toastSpy = { error: vi.fn() };

vi.mock("sonner", () => ({
  toast: { error: (...a: unknown[]) => toastSpy.error(...a) },
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

const mockDocuments = [
  { id: "doc-001", employee_id: "emp-001", document_type: "cccd", file_name: "CMND_scan.pdf", file_size: 204800, mime_type: "application/pdf", description: null, uploaded_at: "2026-01-15T08:00:00Z" },
  { id: "doc-002", employee_id: "emp-001", document_type: "degree", file_name: "Bang_dai_hoc.jpg", file_size: 512000, mime_type: "image/jpeg", description: null, uploaded_at: "2026-02-20T10:30:00Z" },
  { id: "doc-003", employee_id: "emp-001", document_type: "contract", file_name: "Hop_dong_lao_dong_2026.docx", file_size: 1048576, mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document", description: null, uploaded_at: "2026-03-01T14:00:00Z" },
];

let DocumentsPage: React.ComponentType;

beforeEach(async () => {
  mockFetch.mockReset();
  toastSpy.error.mockReset();
  currentUserMock.value = { employee_id: "emp-001" };

  // jsdom doesn't implement URL.createObjectURL / revokeObjectURL
  if (typeof URL.createObjectURL !== "function") {
    URL.createObjectURL = vi.fn(() => "blob:http://localhost/mock") as typeof URL.createObjectURL;
  }
  if (typeof URL.revokeObjectURL !== "function") {
    URL.revokeObjectURL = vi.fn() as typeof URL.revokeObjectURL;
  }

  const mod = await import("../page");
  DocumentsPage = mod.default;
});

describe("EmployeeDocumentsPage", () => {
  it("renders heading", () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    render(<DocumentsPage />);
    expect(screen.getByText("Tài liệu")).toBeInTheDocument();
  });

  it("shows loading skeleton while fetching", () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    render(<DocumentsPage />);
    expect(screen.getByText("Tài liệu")).toBeInTheDocument();
  });

  it("shows empty state when no documents", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] });
    render(<DocumentsPage />);
    await waitFor(() => expect(screen.getByText("Chưa có tài liệu nào.")).toBeInTheDocument());
  });

  it("shows documents in table on success", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockDocuments });
    render(<DocumentsPage />);
    await waitFor(() => expect(screen.getByText("CMND_scan.pdf")).toBeInTheDocument());
    expect(screen.getByText("Bang_dai_hoc.jpg")).toBeInTheDocument();
    expect(screen.getByText("Hop_dong_lao_dong_2026.docx")).toBeInTheDocument();
    expect(screen.getByText("CCCD/CMND")).toBeInTheDocument();
    expect(screen.getByText("Bằng cấp")).toBeInTheDocument();
    expect(screen.getByText("Hợp đồng")).toBeInTheDocument();
    expect(screen.getByText("200.0 KB")).toBeInTheDocument();
    expect(screen.getByText("500.0 KB")).toBeInTheDocument();
    expect(screen.getByText("1.0 MB")).toBeInTheDocument();
  });

  it("downloads document on click", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockDocuments });
    render(<DocumentsPage />);
    await waitFor(() => expect(screen.getByText("CMND_scan.pdf")).toBeInTheDocument());

    mockFetch.mockResolvedValueOnce({ ok: true, blob: async () => new Blob(["fake"]) });

    const buttons = screen.getAllByRole("button", { name: /tải xuống/i });
    buttons[0].click();

    await waitFor(() => expect(mockFetch).toHaveBeenCalledWith("/api/documents/doc-001/download"));
  });

  it("shows error toast on list failure", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });
    render(<DocumentsPage />);
    await waitFor(() => expect(toastSpy.error).toHaveBeenCalledWith("Không thể tải danh sách tài liệu"));
  });

  it("shows error toast on download failure", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockDocuments });
    render(<DocumentsPage />);
    await waitFor(() => expect(screen.getByText("CMND_scan.pdf")).toBeInTheDocument());

    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });
    const buttons = screen.getAllByRole("button", { name: /tải xuống/i });
    buttons[0].click();
    await waitFor(() => expect(toastSpy.error).toHaveBeenCalledWith("Không thể tải xuống tài liệu"));
  });

  it("shows nothing when user has no employee_id", () => {
    currentUserMock.value = { employee_id: null };
    render(<DocumentsPage />);
    expect(screen.getByText("Tài liệu")).toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalled();
  });
});
