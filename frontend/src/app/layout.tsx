import type { Metadata } from "next";
import { Public_Sans } from "next/font/google";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const publicSans = Public_Sans({
  subsets: ["latin", "vietnamese"],
  variable: "--font-public-sans",
  weight: ["300", "400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vroom HR",
  description: "Nền tảng quản lý nhân sự thông minh cho doanh nghiệp Việt Nam",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="vi"
      suppressHydrationWarning
      className={`${publicSans.variable}`}
    >
      <body className="font-sans antialiased">
        <Providers>
          {children}
          <Toaster
            position="bottom-right"
            richColors
            closeButton
            visibleToasts={5}
          />
        </Providers>
      </body>
    </html>
  );
}
