import React from 'react';
import { Inbox } from 'lucide-react';

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------
export function EmptyState({ title, hint, icon }: { title: string; hint?: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 px-4">
      <div className="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-2">
        {icon ?? <Inbox className="w-6 h-6 text-slate-300" />}
      </div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {hint && <p className="text-xs text-slate-400 mt-1 max-w-xs">{hint}</p>}
    </div>
  );
}
