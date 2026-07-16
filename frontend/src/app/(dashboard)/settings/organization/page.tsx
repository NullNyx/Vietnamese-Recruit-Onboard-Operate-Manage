"use client";

import { useState, useEffect } from "react";
import { Plus, Trash2, Shield, AlertCircle, CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  getNetworkAllowlist,

  addNetworkToAllowlist,
  removeNetworkFromAllowlist,
} from "@/lib/api/attendance";

function isValidCIDR(cidr: string): boolean {
  const regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-9]|[12][0-9]|3[0-2])$/;
  return regex.test(cidr.trim());
}

export default function OrganizationSettingsPage() {
  const [networks, setNetworks] = useState<string[]>([]);
  const [newCidr, setNewCidr] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    loadNetworks();
  }, []);

  const loadNetworks = async () => {
    try {
      setLoading(true);
      const data = await getNetworkAllowlist();
      setNetworks(data.networks || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load networks");
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    const trimmed = newCidr.trim();
    if (!trimmed) return;

    if (!isValidCIDR(trimmed)) {
      setError("Định dạng CIDR không hợp lệ. Ví dụ: 192.168.1.0/24");
      return;
    }

    if (networks.includes(trimmed)) {
      setError("CIDR này đã tồn tại trong danh sách");
      return;
    }

    if (networks.length >= 20) {
      setError("Tối đa 20 CIDR. Vui lòng xóa bớt trước khi thêm mới.");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const data = await addNetworkToAllowlist([trimmed]);
      setNetworks(data.networks);
      setNewCidr("");
      setSuccess("Đã thêm CIDR thành công");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add network");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async (cidr: string) => {
    try {
      setSaving(true);
      setError(null);
      const data = await removeNetworkFromAllowlist(cidr);
      setNetworks(data.networks);
      setSuccess("Đã xóa CIDR thành công");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove network");
    } finally {
      setSaving(false);
    }
  };

      return (
        <div className="animate-fade-in space-y-6">
          {/* Header */}
          <div className="fade-in-section">
            <h1 className="font-heading text-2xl font-bold text-foreground tracking-tight">
              Cấu hình tổ chức
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Quản lý cấu hình mạng và các thiết lập khác cho tổ chức
            </p>
          </div>

          {/* Office Network Allowlist */}
          <div className="fade-in-section">
            <Card className="card-hover">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  <CardTitle>Mạng văn phòng</CardTitle>
                </div>
                <CardDescription>
                  Cấu hình danh sách IP/CIDR được phép để nhân viên chấm công.
                  Để trống cho phép tất cả các IP.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Alerts */}
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                {success && (
                  <Alert variant="default" className="bg-success/10 border-success/20 text-success-foreground">
                    <CheckCircle2 className="h-4 w-4 text-success" />
                    <AlertDescription className="text-success">{success}</AlertDescription>
                  </Alert>
                )}

                {/* Input row */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Nhập CIDR: 192.168.1.0/24"
                    value={newCidr}
                    onChange={(e) => setNewCidr(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                    disabled={saving}
                    className="max-w-xs"
                  />
                  <Button onClick={handleAdd} disabled={saving || !newCidr.trim()}>
                    <Plus className="mr-2 h-4 w-4" />
                    Thêm
                  </Button>
                </div>

                {/* Network list */}
                {loading ? (
                  <div className="text-sm text-muted-foreground">Đang tải...</div>
                ) : networks.length === 0 ? (
                  <div className="text-sm text-muted-foreground py-8 text-center rounded-lg border border-dashed border-border/50">
                    Chưa có CIDR nào. Nhân viên có thể chấm công từ bất kỳ IP nào.
                  </div>
                ) : (
                  <div className="rounded-lg border overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>CIDR</TableHead>
                          <TableHead className="text-right">Thao tác</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {networks.map((cidr) => (
                          <TableRow key={cidr} className="card-hover">
                            <TableCell className="font-mono text-sm">{cidr}</TableCell>
                            <TableCell className="text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRemove(cidr)}
                                disabled={saving}
                                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {/* Stats */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="outline">
                    {networks.length} / 20 CIDR
                  </Badge>
                  {networks.length === 0 && (
                    <span className="text-amber-600 dark:text-amber-400">Chế độ cho phép tất cả</span>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
  );
}
