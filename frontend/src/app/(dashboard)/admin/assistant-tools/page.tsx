"use client";

import { useEffect, useState } from "react";
import { Bot, Search, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  listAssistantTools,
  updateAssistantTools,
  type AssistantToolConfig,
} from "@/lib/api/admin";

export default function AssistantToolsPage() {
  const [tools, setTools] = useState<AssistantToolConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [pendingChanges, setPendingChanges] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      const res = await listAssistantTools();
      setTools(res.tools);
    } catch (err) {
      toast.error(
        `Lỗi: ${err instanceof Error ? err.message : "Không thể tải danh sách tool"}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (toolName: string) => {
    const tool = tools.find((t) => t.tool_name === toolName);
    if (!tool) return;
    const current = pendingChanges[toolName] !== undefined ? pendingChanges[toolName] : tool.enabled;
    setPendingChanges((prev) => ({
      ...prev,
      [toolName]: !current,
    }));
  };

  const handleApply = async () => {
    setSaving(true);
    try {
      // Build the full tool config: merge pending changes with current state
      const toolConfigs: Record<string, boolean> = {};
      for (const tool of tools) {
        const pending = pendingChanges[tool.tool_name];
        toolConfigs[tool.tool_name] = pending !== undefined ? pending : tool.enabled;
      }

      await updateAssistantTools(toolConfigs);

      // Update local state with applied changes
      setTools((prev) =>
        prev.map((tool) => ({
          ...tool,
          enabled: toolConfigs[tool.tool_name],
        }))
      );
      setPendingChanges({});

      toast.success("Đã áp dụng cấu hình tool!");
    } catch (err) {
      toast.error(
        `Lỗi: ${err instanceof Error ? err.message : "Không thể lưu cấu hình"}`
      );
    } finally {
      setSaving(false);
    }
  };

      const filteredTools = tools.filter(
        (tool) =>
          tool.display_name.toLowerCase().includes(search.toLowerCase()) ||
          tool.tool_name.toLowerCase().includes(search.toLowerCase()) ||
          tool.description.toLowerCase().includes(search.toLowerCase())
      );

  const hasPendingChanges = Object.keys(pendingChanges).length > 0;

  // Preview state: show what would change
  const getPreviewEnabled = (tool: AssistantToolConfig) => {
    const pending = pendingChanges[tool.tool_name];
    return pending !== undefined ? pending : tool.enabled;
  };

      if (loading) {
        return (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        );
      }

      return (
        <div className="animate-fade-in space-y-6">
          <div className="fade-in-section">
            <h1 className="text-2xl font-bold tracking-tight">Cấu hình AI Assistant</h1>
            <p className="text-muted-foreground">
              Quản lý các tool mà AI Assistant có thể sử dụng
            </p>
          </div>

          {/* Search + Apply */}
          <div className="fade-in-section flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Tìm tool theo tên hoặc mô tả..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button
              onClick={handleApply}
              disabled={!hasPendingChanges || saving}
            >
              {saving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Áp dụng
            </Button>
          </div>

          {/* Pending changes indicator */}
          {hasPendingChanges && (
            <div className="fade-in-section rounded-xl bg-accent/10 border border-accent/20 p-4 text-sm text-accent-foreground">
              <span className="font-medium">ℹ</span> Có {Object.keys(pendingChanges).length} thay đổi chưa áp dụng. Nhấn
              &quot;Áp dụng&quot; để lưu.
            </div>
          )}

          {/* Tool list */}
          <div className="fade-in-section space-y-3">
            {filteredTools.length === 0 ? (
              <p className="text-center py-12 text-muted-foreground">
                {search ? "Không tìm thấy tool phù hợp" : "Không có tool nào"}
              </p>
            ) : (
              filteredTools.map((tool) => {
                const previewEnabled = getPreviewEnabled(tool);
                const isChanged = pendingChanges[tool.tool_name] !== undefined;

                return (
                  <Card key={tool.tool_name} className={`card-hover ${isChanged ? "ring-1 ring-accent" : ""}`}>
                    <CardContent className="flex items-center gap-4 py-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                        <Bot className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                              <span className="font-medium">{tool.display_name}</span>
                              <Badge variant={tool.kind === "read" ? "secondary" : "default"}>
                                {tool.kind === "read" ? "Tool đọc" : "Tool soạn thảo"}
                          </Badge>
                          {isChanged && (
                            <Badge variant="outline" className="text-accent border-accent/30">
                              Chưa lưu
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {tool.description}
                        </p>
                      </div>
                      <button
                        onClick={() => handleToggle(tool.tool_name)}
                        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                          previewEnabled ? "bg-primary" : "bg-muted"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform ${
                            previewEnabled ? "translate-x-5" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </div>
        </div>
  );
}
