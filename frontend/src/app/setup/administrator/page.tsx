'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { createAdmin } from '@/lib/api/setup';

export default function SetupAdminPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!name || !email || !password) {
      setError('Vui lòng điền đầy đủ thông tin');
      return;
    }
    if (password.length < 8) {
      setError('Mật khẩu phải có ít nhất 8 ký tự');
      return;
    }
    setLoading(true);
    try {
      await createAdmin({ email, password, name });
      router.push('/setup/organization');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lỗi tạo tài khoản');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[520px] rounded-2xl border border-[#E4E4E7] bg-white p-10 shadow-sm">
      <div className="space-y-6">
        <div className="space-y-1 text-center">
          <h1 className="text-lg font-bold text-[#09090B]">
            Tạo tài khoản quản trị
          </h1>
          <p className="text-sm text-[#71717A]">
            Tài khoản đầu tiên được gán quyền{' '}
            <strong>Super Admin</strong> — quyền cao nhất trong hệ thống.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Họ và tên</Label>
            <Input
              placeholder="Nguyễn Văn A"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input
              type="email"
              placeholder="admin@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Mật khẩu</Label>
            <Input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <p className="text-[10px] text-[#71717A]">Tối thiểu 8 ký tự</p>
          </div>

          {error && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3">
              <p className="text-xs text-destructive">{error}</p>
            </div>
          )}

          <Button type="submit" className="w-full" size="lg" disabled={loading}>
            {loading ? 'Đang xử lý…' : 'Tiếp tục'}
          </Button>
        </form>
      </div>
    </div>
  );
}
