import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AEO Platform",
  description: "Answer Engine Optimization + SEO + Competitor Intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "AEO Platform";
  return (
    <html lang="en">
      <body>
        <header className="border-b border-white/10">
          <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
            <a href="/" className="font-semibold tracking-tight text-lg">
              <span className="text-accent">●</span> {appName}
            </a>
            <nav className="text-sm text-slate-400 flex gap-5">
              <a href="/" className="hover:text-white">Agents</a>
              <a href="/history" className="hover:text-white">History</a>
              <a href="http://localhost:8000/docs" className="hover:text-white" target="_blank">
                API
              </a>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
