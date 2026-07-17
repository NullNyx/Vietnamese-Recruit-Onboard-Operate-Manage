import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "vietnamese"],
  variable: "--font-inter",
  weight: ["300", "400", "500", "600", "700"],
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
      className={`${inter.variable}`}
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
