import type { Metadata } from "next";
import { Fraunces, Public_Sans, Space_Grotesk } from "next/font/google";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin", "vietnamese"],
  variable: "--font-fraunces",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const publicSans = Public_Sans({
  subsets: ["latin", "vietnamese"],
  variable: "--font-public-sans",
  weight: ["300", "400", "500", "600"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin", "vietnamese"],
  variable: "--font-space-grotesk",
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vroom HR",
  description: "Nền tảng quản lý nhân sự thông minh cho doanh nghiệp Việt Nam",
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
      className={`${fraunces.variable} ${publicSans.variable} ${spaceGrotesk.variable}`}
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
