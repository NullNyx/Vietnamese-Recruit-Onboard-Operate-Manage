"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UserPlus, FileSpreadsheet } from "lucide-react";

import { DataTable, type ColumnDef } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { employeesApi, departmentsApi, positionsApi } from "@/lib/api";
import type { Employee, Department, Position } from "@/lib/api/types";

interface EmployeeRow extends Record<string, unknown> {
  id: string;
  full_name: string;
  email: string;
  department_name: string;
  position_name: string;
  is_active: boolean;
}

const columns: ColumnDef<EmployeeRow>[] = [
  { key: "full_name", header: "Họ tên" },
  { key: "email", header: "Email" },
  { key: "department_name", header: "Phòng ban" },
  { key: "position_name", header: "Chức vụ" },
  {
    key: "is_active",
    header: "Trạng thái",
    cell: (row) => (
      <span
        className={
          row.is_active
            ? "text-green-600 dark:text-green-400"
            : "text-muted-foreground"
        }
      >
        {row.is_active ? "Đang làm" : "Đã nghỉ"}
      </span>
    ),
  },
];

export default function EmployeesPage() {
  const router = useRouter();

  const [data, setData] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");

  // Fetch departments and positions once for name lookups
  useEffect(() => {
    departmentsApi.listDepartments().then(setDepartments).catch(() => {});
    positionsApi.listPositions().then(setPositions).catch(() => {});
  }, []);

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await employeesApi.listEmployees({
        page,
        page_size: pageSize,
        search: search || undefined,
      });
      setData(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Không thể tải danh sách nhân viên"
      );
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  // Map employees to rows with department/position names
  const rows: EmployeeRow[] = useMemo(() => {
    const deptMap = new Map(departments.map((d) => [d.id, d.name]));
    const posMap = new Map(positions.map((p) => [p.id, p.name]));

    return data.map((emp) => ({
      id: emp.id,
      full_name: emp.full_name,
      email: emp.email,
      department_name: emp.department_id
        ? deptMap.get(emp.department_id) ?? "—"
        : "—",
      position_name: emp.position_id
        ? posMap.get(emp.position_id) ?? "—"
        : "—",
      is_active: emp.is_active,
    }));
  }, [data, departments, positions]);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handlePageSizeChange = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  const handleRowClick = useCallback(
    (row: EmployeeRow) => {
      router.push(`/employees/${row.id}`);
    },
    [router]
  );

  const toolbar = (
    <>
      <Link href="/employees/import">
        <Button variant="outline" size="sm">
          <FileSpreadsheet className="mr-2 h-4 w-4" aria-hidden="true" />
          Import Excel
        </Button>
      </Link>
      <Link href="/employees/new">
        <Button size="sm">
          <UserPlus className="mr-2 h-4 w-4" aria-hidden="true" />
          Thêm nhân viên
        </Button>
      </Link>
    </>
  );

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Nhân viên</h1>
        <p className="text-sm text-muted-foreground">
          Quản lý danh sách nhân viên trong tổ chức
        </p>
      </div>

      <DataTable<EmployeeRow>
        columns={columns}
        data={rows}
        loading={loading}
        error={error}
        pagination={{ page, pageSize, total }}
        searchPlaceholder="Tìm kiếm theo tên hoặc email..."
        onSearch={handleSearch}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        onRowClick={handleRowClick}
        toolbar={toolbar}
      />
    </div>
  );
}
