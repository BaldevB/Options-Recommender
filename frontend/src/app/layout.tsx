import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Options Suggester Pro | Next.js Financial Terminal",
  description: "High-Conviction Stock Options Signals, TradingView Charts, and AI Sector Ecosystem",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#070b12] text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
