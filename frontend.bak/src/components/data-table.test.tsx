/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DataTable } from "./data-table";

type Row = { id: string; name: string };
const columns = [
  { key: "name", header: "Tên" },
];

function renderTable(props: Partial<React.ComponentProps<typeof DataTable<Row>>> = {}) {
  return render(
    <DataTable<Row>
      columns={columns}
      data={[]}
      {...props}
    />,
  );
}

describe("DataTable states", () => {
  it("keeps loading distinct from empty data", () => {
    renderTable({ loading: true });

    expect(screen.queryByText("Chưa có bản ghi nào trong phạm vi này.")).not.toBeInTheDocument();
  });

  it("explains empty filtered results", () => {
    renderTable({ onSearch: vi.fn() });
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "không tồn tại" } });

    expect(screen.getAllByText("Không tìm thấy dữ liệu phù hợp với bộ lọc hiện tại.")).toHaveLength(2);
  });

  it("offers retry for errors", () => {
    const onRetry = vi.fn();
    renderTable({ error: "Máy chủ không phản hồi", onRetry });

    fireEvent.click(screen.getAllByRole("button", { name: "Thử lại" })[0]);

    expect(screen.getAllByText("Lỗi tải dữ liệu: Máy chủ không phản hồi")).toHaveLength(2);
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
