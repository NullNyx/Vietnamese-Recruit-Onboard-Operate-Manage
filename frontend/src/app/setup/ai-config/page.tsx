'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { configureAi } from '@/lib/api/setup';

const providers = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'compatible', label: 'OpenAI-compatible endpoint' },
  { value: 'local', label: 'Local LLM' },
  { value: 'disabled', label: 'Disabled' },
];

export default function SetupAiConfigPage() {
  const router = useRouter();
  const [provider, setProvider] = useState('disabled');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await configureAi({ provider, api_key: apiKey || null });
      router.push('/setup/templates');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lỗi cấu hình AI');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[520px] rounded-2xl border border-[#E4E4E7] bg-white p-10 shadow-sm">
      <div className="space-y-6">
        <div className="space-y-1 text-center">
          <h1 className="text-lg font-bold text-[#09090B]">Cấu hình AI</h1>
          <p className="text-sm text-[#71717A]">
            AI là tuỳ chọn. Có thể để Disabled và bật sau trong admin.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Nhà cung cấp</Label>
            <Select value={provider} onValueChange={setProvider} disabled={loading}>
              <SelectTrigger>
                <SelectValue placeholder="Chọn provider" />
              </SelectTrigger>
              <SelectContent>
                {providers.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>API key</Label>
            <Input value={apiKey} onChange={(e) => setApiKey(e.target.value)} disabled={loading} />
          </div>

          {error && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3">
              <p className="text-xs text-destructive">{error}</p>
            </div>
          )}

          <div className="flex gap-3">
            <Button type="button" variant="outline" className="flex-1" onClick={() => router.push('/setup/organization')}>
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
