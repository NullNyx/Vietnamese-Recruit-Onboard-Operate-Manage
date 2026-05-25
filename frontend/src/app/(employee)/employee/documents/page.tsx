"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { FileText, Download, Filter } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { essApi } from "@/lib/api";
import type { ESSDocument } from "@/lib/api/ess";

const ALL_TYPES = "__all__";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(isoString: string): string {
  const d = new Date(isoString);
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "Asia/Ho_Chi_Minh",
  });
}

function formatDocumentType(type: string): string {
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function EmployeeDocumentsPage() {
  const [documents, setDocuments] = useState<ESSDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>(ALL_TYPES);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await essApi.getDocuments();
      setDocuments(data);
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const documentTypes = useMemo(() => {
    const types = new Set(documents.map((doc) => doc.document_type));
    return Array.from(types).sort();
  }, [documents]);

  const filteredDocuments = useMemo(() => {
    if (selectedType === ALL_TYPES) return documents;
    return documents.filter((doc) => doc.document_type === selectedType);
  }, [documents, selectedType]);

  async function handleDownload(documentId: string) {
    setDownloadingId(documentId);
    try {
      const { download_url } = await essApi.getDocumentDownloadUrl(documentId);
      window.open(download_url, "_blank", "noopener,noreferrer");
    } catch {
      // Silently fail - user can retry
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Tài liệu</h1>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Tài liệu cá nhân
            </CardTitle>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Lọc theo loại" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_TYPES}>Tất cả</SelectItem>
                  {documentTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {formatDocumentType(type)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
              <p className="text-muted-foreground text-sm">
                {selectedType === ALL_TYPES
                  ? "Không có tài liệu nào."
                  : "Không có tài liệu nào cho loại đã chọn."}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tên tệp</TableHead>
                    <TableHead>Loại</TableHead>
                    <TableHead>Kích thước</TableHead>
                    <TableHead>Ngày tải lên</TableHead>
                    <TableHead className="text-right">Thao tác</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDocuments.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium">
                        {doc.file_name}
                      </TableCell>
                      <TableCell>
                        {formatDocumentType(doc.document_type)}
                      </TableCell>
                      <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                      <TableCell>{formatDate(doc.uploaded_at)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownload(doc.id)}
                          disabled={downloadingId === doc.id}
                        >
                          <Download className="h-4 w-4 mr-1" />
                          {downloadingId === doc.id
                            ? "Đang tải..."
                            : "Tải xuống"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
