import type { Metadata } from "next";
import { Sidebar } from "@/components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "RedTag | Autonomous Recall Command Center",
  description: "Observe, reason, act, recover, verify and prove product recall operations."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><div className="shell"><Sidebar/><main className="main">{children}</main></div></body></html>;
}
