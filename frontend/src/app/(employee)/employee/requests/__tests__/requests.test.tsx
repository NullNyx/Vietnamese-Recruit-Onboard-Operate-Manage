/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import RequestsPage from "../page";

describe("EmployeeRequestsPage", () => {
  it("renders heading", () => {
    render(<RequestsPage />);

    expect(screen.getByText("Yêu cầu của tôi")).toBeInTheDocument();
  });

  it("shows both request type cards", () => {
    render(<RequestsPage />);

    expect(screen.getByText("Đơn nghỉ phép")).toBeInTheDocument();
    expect(screen.getByText("Đơn tăng ca")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    render(<RequestsPage />);

    expect(screen.getByText("Chưa có yêu cầu nào")).toBeInTheDocument();
  });

  it("has create button linking to new request", () => {
    render(<RequestsPage />);

    const createLink = screen.getByText("Tạo yêu cầu").closest("a");
    expect(createLink).toHaveAttribute("href", "/employee/requests/new");
  });
});
