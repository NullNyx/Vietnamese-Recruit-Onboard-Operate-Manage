"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DataTable, type ColumnDef } from "@/components/data-table";
import { listPositions } from "@/lib/api/positions";
import { listDepartments } from "@/lib/api/departments";

interface PositionRow {
  id: string;
  name: string;
  department_name: string;
  description: string;
  [key: string]: unknown;
}

export default function PositionsPage() {
  const [positions, setPositions] = useState<PositionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [positionsList, departmentsList] = await Promise.all([
        listPositions(),
        listDepartments(),
      ]);

      // Build department lookup map
      const deptMap: Record<string, string> = {};
      for (const dept of departmentsList) {
        deptMap[dept.id] = dept.name;
      }

      const rows: PositionRow[] = positionsList.map((pos) => ({
        id: pos.id,
        name: pos.name,
        department_name: pos.department_id
          ? deptMap[pos.department_id] || "—"
          : "—",
        description: "—",
      }));

      setPositions(rows);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Không thể tải danh sách chức vụ"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const columns: ColumnDef<PositionRow>[] = [
    {
      key: "name",
      header: "Tên chức vụ",
    },
    {
      key: "department_name",
      header: "Phòng ban",
    },
    {
      key: "description",
      header: "Mô tả",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-heading text-2xl font-bold text-foreground">
          Chức vụ
        </h1>
        <p className="text-sm text-muted-foreground">
          Quản lý danh sách chức vụ trong tổ chức
        </p>
      </div>

      {/* DataTable */}
      <DataTable
        columns={columns}
        data={positions}
        loading={loading}
        error={error}
        toolbar={
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
            Thêm mới
          </Button>
        }
      />
    </div>
  );
}
