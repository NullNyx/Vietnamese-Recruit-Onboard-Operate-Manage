import type { Metadata } from 'next';
import { Be_Vietnam_Pro, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Toaster } from 'sonner';

const beVietnamPro = Be_Vietnam_Pro({
  subsets: ['vietnamese', 'latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-sans',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'Vroom HR — Nền tảng quản trị nhân sự dành cho doanh nghiệp Việt Nam',
  description: 'Giải pháp nhân sự toàn diện: tuyển dụng, chấm công, tính lương, quản lý hồ sơ — tất cả trong một nền tảng.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${beVietnamPro.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <body className="font-sans antialiased text-slate-800 bg-slate-50/50" suppressHydrationWarning>
        <Providers>
          {children}
        </Providers>
        <Toaster position="top-right" richColors closeButton />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  document.querySelectorAll('[bis_skin_checked]').forEach(function(el) {
                    el.removeAttribute('bis_skin_checked');
                  });
                  var observer = new MutationObserver(function(mutations) {
                    for (var i = 0; i < mutations.length; i++) {
                      var m = mutations[i];
                      if (m.type === 'attributes' && m.attributeName === 'bis_skin_checked') {
                        m.target.removeAttribute('bis_skin_checked');
                      }
                    }
                  });
                  observer.observe(document.documentElement, {
                    attributes: true,
                    subtree: true,
                    attributeFilter: ['bis_skin_checked']
                  });
                } catch(e) {}
              })();
            `,
          }}
        />
      </body>
    </html>
  );
}
