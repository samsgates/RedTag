import Link from "next/link";
import { SignOut } from "@/components/sign-out";
import { Activity, Bot, Boxes, CheckCircle2, FileWarning, Network, Settings, ShieldCheck } from "lucide-react";

const items = [
  ["Command Center", "/", Activity],
  ["Incidents", "/incidents", FileWarning],
  ["Agent Fleet", "/agents", Bot],
  ["Approvals", "/approvals", CheckCircle2],
  ["Proof Graph", "/proof", Network],
  ["Operations", "/operations", Boxes],
  ["Security", "/security", ShieldCheck],
  ["Settings", "/settings", Settings],
] as const;

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand"><span className="brandMark">R</span><div><strong>RedTag</strong><small>Recall Command</small></div></div>
      <nav>
        {items.map(([label, href, Icon]) => (
          <Link key={label} href={href} className="navItem">
            <Icon size={18} /><span>{label}</span>
          </Link>
        ))}
      </nav>
      <div className="sideFooter"><div><span className="liveDot"/> Agent fleet online</div><SignOut/></div>
    </aside>
  );
}
