import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Stockboy - LLM Trading Bot Benchmark",
  description: "Benchmark LLM agents on stock trading decisions based on insider trading data",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100 min-h-screen`}>
        <div className="flex">
          <Sidebar />
          <main className="flex-1 ml-64">
            <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
              {/* Subtle gradient orbs for visual interest */}
              <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl" />
                <div className="absolute top-1/2 -left-20 w-60 h-60 bg-teal-500/10 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 right-1/3 w-80 h-80 bg-cyan-500/5 rounded-full blur-3xl" />
              </div>
              <div className="relative z-10 p-8">
                {children}
              </div>
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
