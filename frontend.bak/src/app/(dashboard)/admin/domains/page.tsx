"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { RefreshCw, Globe } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import DomainTable from "@/components/admin/domain-table";
import DomainAddForm from "@/components/admin/domain-add-form";
import {
  listDomains,
  addDomains,
  removeDomain,
} from "@/lib/api/admin";

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function DomainsPage() {
  const [domains, setDomains] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDomains = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listDomains();
      setDomains(response.allowed_domains);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Không thể tải danh sách domain";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDomains();
  }, [fetchDomains]);

  const handleAdd = useCallback(
    async (domain: string) => {
      try {
        await addDomains([domain]);
        toast.success(`Đã thêm "${domain}" vào danh sách`);
        await fetchDomains();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Không thể thêm domain";
        toast.error(message);
        throw err;
      }
    },
    [fetchDomains]
  );

  const handleDelete = useCallback(
    async (domain: string) => {
      try {
        await removeDomain(domain);
        toast.success(`Đã xóa "${domain}" khỏi danh sách`);
        await fetchDomains();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Không thể xóa domain";
        toast.error(message);
      }
    },
    [fetchDomains]
  );

      return (
        <div className="animate-fade-in space-y-6">
          {/* Header */}
          <div className="fade-in-section flex items-center justify-between">
            <div>
              <h1 className="font-heading text-2xl font-bold text-foreground tracking-tight">
                Quản lý domain đăng nhập
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Danh sách email domain được phép đăng nhập vào hệ thống
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDomains}
              disabled={loading}
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
                aria-hidden="true"
              />
              Làm mới
            </Button>
          </div>

          {/* Info */}
          <div className="fade-in-section">
            <Card className="border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/30 card-hover">
              <CardContent className="flex items-start gap-4 py-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/50">
                  <Globe className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="text-sm text-blue-800 dark:text-blue-200">
                  <p className="font-medium">Cách hoạt động</p>
                  <p className="mt-1 text-blue-700 dark:text-blue-300">
                    Khi danh sách trống, mọi email đều được phép đăng nhập. Khi có
                    domain trong danh sách, chỉ email thuộc các domain được phép mới
                    có thể đăng nhập.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Add Form */}
          <div className="fade-in-section">
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">+</span>
                  Thêm domain mới
                </CardTitle>
              </CardHeader>
              <CardContent>
                <DomainAddForm onAdd={handleAdd} />
              </CardContent>
            </Card>
          </div>

          {/* Table */}
          <div className="fade-in-section">
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="text-base">
                  Danh sách domain
                  {!loading && (
                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                      ({domains.length} domain)
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div aria-live="polite" aria-atomic="true">
                  <DomainTable
                    domains={domains}
                    loading={loading}
                    onDelete={handleDelete}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
  );
}
