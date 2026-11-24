import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CyberLab | Hybrid SOC & Simulation Platform",
  description: "Next-generation Hybrid Cybersecurity Infrastructure, Network Simulation, Endpoint Security & SOC Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
