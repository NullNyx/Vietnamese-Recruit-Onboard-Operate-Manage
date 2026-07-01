'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { configureOrg } from '@/lib/api/setup';

export default function SetupOrganizationPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [taxCode, setTaxCode] = useState('');
  const [timezone, setTimezone] = useState('Asia/Ho_Chi_Minh');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!name || !taxCode || !timezone) {
      setError('Vui lòng điền đầy đủ thông tin');
      return;
    }
    setLoading(true);
    try {
      await configureOrg({ name, tax_code: taxCode, timezone });
      router.push('/setup/ai-config');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lỗi cấu hình tổ chức');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[520px] rounded-2xl border border-[#E4E4E7] bg-white p-10 shadow-sm">
      <div className="space-y-6">
        <div className="space-y-1 text-center">
          <h1 className="text-lg font-bold text-[#09090B]">Thông tin tổ chức</h1>
          <p className="text-sm text-[#71717A]">
            Nhập dữ liệu công ty để hệ thống hiển thị đúng bối cảnh vận hành.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Tên công ty</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} disabled={loading} />
          </div>
          <div className="space-y-1.5">
            <Label>Mã số thuế</Label>
            <Input value={taxCode} onChange={(e) => setTaxCode(e.target.value)} disabled={loading} />
          </div>
          <div className="space-y-1.5">
            <Label>Timezone</Label>
            <Input value={timezone} onChange={(e) => setTimezone(e.target.value)} disabled={loading} />
          </div>

          {error && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3">
              <p className="text-xs text-destructive">{error}</p>
            </div>
          )}

          <div className="flex gap-3">
            <Button type="button" variant="outline" className="flex-1" onClick={() => router.push('/setup/administrator')}>
              Quay lại
            </Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? 'Đang xử lý…' : 'Tiếp tục'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
