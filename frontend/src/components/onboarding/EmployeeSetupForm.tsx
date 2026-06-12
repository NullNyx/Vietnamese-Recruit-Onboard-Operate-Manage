'use client';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { listDepartments } from '@/lib/api/departments';
import { listEmployees } from '@/lib/api/employees';
import { onboardingKeys, OnboardingProcess, updateEmployeeSetup } from '@/lib/api/onboarding';
import { listPositions } from '@/lib/api/positions';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

export function EmployeeSetupForm({ process }: { process: OnboardingProcess }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    department_id: process.department_id || '',
    position_id: process.position_id || '',
    manager_id: process.manager_id || '',
    start_date: process.start_date || '',
  });

  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: listDepartments,
  });

  const { data: positions } = useQuery({
    queryKey: ['positions'],
    queryFn: listPositions,
  });

  const { data: employeesData } = useQuery({
    queryKey: ['employees', { is_active: true }],
    queryFn: () => listEmployees({ is_active: true, page_size: 1000 }),
  });
  const managers = employeesData?.items || [];

  const updateMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      updateEmployeeSetup(process.id, {
        department_id: data.department_id || null,
        position_id: data.position_id || null,
        manager_id: data.manager_id || null,
        start_date: data.start_date || null,
      }),
    onSuccess: (updatedProcess) => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.detail(process.id) });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.lists() });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.counts() });

      if (updatedProcess.status === 'complete') {
        toast.success('Thiết lập hoàn tất. Nhân viên đã được kích hoạt!');
      } else {
        toast.success('Đã lưu thông tin thiết lập');
      }
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Lưu thất bại');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const isComplete = process.status === 'complete';
  const hasMissing = process.missing_setup_fields && process.missing_setup_fields.length > 0;

  return (
    <div className="space-y-4 p-6 border-b bg-muted/10">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Thiết lập nhân viên</h3>
      </div>

      {!isComplete && hasMissing && (
        <Alert
          variant="destructive"
          className="bg-destructive/5 text-destructive border-destructive/20"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">
            Vui lòng hoàn thiện các trường sau để kích hoạt nhân viên:{' '}
            <span className="font-semibold">{process.missing_setup_fields.join(', ')}</span>
          </AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Phòng ban</Label>
            <Select
              disabled={isComplete || updateMutation.isPending}
              value={formData.department_id}
              onValueChange={(val) => setFormData({ ...formData, department_id: val })}
            >
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Chọn phòng ban" />
              </SelectTrigger>
              <SelectContent>
                {departments?.map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Vị trí</Label>
            <Select
              disabled={isComplete || updateMutation.isPending}
              value={formData.position_id}
              onValueChange={(val) => setFormData({ ...formData, position_id: val })}
            >
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Chọn vị trí" />
              </SelectTrigger>
              <SelectContent>
                {positions
                  ?.filter(
                    (p) => !formData.department_id || p.department_id === formData.department_id,
                  )
                  .map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Người quản lý</Label>
            <Select
              disabled={isComplete || updateMutation.isPending}
              value={formData.manager_id}
              onValueChange={(val) => setFormData({ ...formData, manager_id: val })}
            >
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Chọn quản lý" />
              </SelectTrigger>
              <SelectContent>
                {managers.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    {m.full_name} ({m.employee_code || m.email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Ngày bắt đầu</Label>
            <Input
              type="date"
              className="h-9"
              disabled={isComplete || updateMutation.isPending}
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            />
          </div>
        </div>

        {!isComplete && (
          <div className="flex justify-end pt-2">
            <Button type="submit" size="sm" disabled={updateMutation.isPending}>
              {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Lưu thiết lập
            </Button>
          </div>
        )}
      </form>
    </div>
  );
}
