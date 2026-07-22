'use client';

import React from 'react';
import { useLocale } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';

/**
 * Locale switcher pill — toggles between VI / EN.
 * Sets NEXT_LOCALE cookie, replaces locale in path, and refreshes.
 */
export default function LocaleSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  const toggleLocale = () => {
    const nextLocale = locale === 'vi' ? 'en' : 'vi';
    // Replace locale prefix in the path
    const newPath = pathname.replace(/^\/(vi|en)/, `/${nextLocale}`);
    document.cookie = `NEXT_LOCALE=${nextLocale}; path=/; max-age=${365 * 24 * 60 * 60}`;
    router.replace(newPath);
    router.refresh();
  };

  return (
    <button
      onClick={toggleLocale}
      className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 hover:text-indigo-600 transition-all shrink-0"
      title={locale === 'vi' ? 'Switch to English' : 'Chuyển sang Tiếng Việt'}
    >
      <span className={`${locale === 'vi' ? 'text-indigo-600 font-bold' : 'text-slate-400'}`}>VI</span>
      <span className="text-slate-300">/</span>
      <span className={`${locale === 'en' ? 'text-indigo-600 font-bold' : 'text-slate-400'}`}>EN</span>
    </button>
  );
}
